"""Turn an approved "Suggest a change" issue into a seed edit (run by .github/workflows/issue-to-pr.yml).

Reads the issue form body from $ISSUE_BODY and writes:
  - a link-out to venue_actions.csv, or a confirmation to venue_confirmations.csv, when the venue name + city match a row in
    manual_venues.csv (the only venues the seeds can address by key);
  - for "Report a sport" / "Confirm" on any other pin (found by its map id in app/data/venues.json): a manual_venues row at the
    pin's coordinates with confirmation 'reported', which the build merges onto that pin (int_manual_venue_match), plus the
    reporter's row in venue_confirmations.csv. The map id is used once, here; the new venue_key is the stable key after that;
  - otherwise a lead in venue_leads.csv, so a reviewer can place it. Leads are not shown on the map. Corrections and closures
    always become leads: one unverified report never removes or changes a venue.
The issue text is untrusted: it is only ever written through the csv module, URLs must be https, and nothing is executed.
Prints a one-line summary on success; exits 1 with a reason on bad input.
"""
import csv, json, os, re, sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "transform" / "seeds"
VENUES_JSON = ROOT / "app" / "data" / "venues.json"
LINK_TYPES = {"Open play": "open_play", "Drop-in": "drop_in", "Clinic": "clinic", "Group class": "group_class",
              "Private lesson": "private_lesson", "League": "league", "Tournament": "tournament", "Social event": "social_event",
              "Court booking": "court_booking", "Club page": "club_page"}


def fail(msg):
    print(msg)
    sys.exit(1)


def parse_form(body):
    """GitHub issue forms render as '### Label' followed by the answer."""
    out, key = {}, None
    for line in body.replace("\r", "").split("\n"):
        if line.startswith("### "):
            key = line[4:].strip()
            out[key] = ""
        elif key is not None:
            out[key] += line + "\n"
    return {k: ("" if v.strip() == "_No response_" else v.strip()) for k, v in out.items()}


def field(form, prefix):
    for k, v in form.items():
        if k.startswith(prefix):
            return v
    return ""


def clean(s, n=1500):
    return re.sub(r"\s+", " ", s).strip()[:n]


def append(name, row):
    path = SEEDS / name
    data = path.read_bytes()
    eol = "\r\n" if b"\r\n" in data else "\n"   # keep the file's own line endings (mixed endings break DuckDB's CSV sniffer)
    with path.open("a", newline="", encoding="utf-8") as f:
        if not data.endswith(b"\n"):
            f.write(eol)
        csv.writer(f, lineterminator=eol).writerow(row)


def read_seed(name):
    with (SEEDS / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def canonical_sport(text):
    """Sport name as the sheet spells it (all_racquet.csv or a sport_aliases.csv alias), or None."""
    want = text.strip().lower()
    for r in read_seed("all_racquet.csv"):
        if r["sport"].strip().lower() == want:
            return r["sport"].strip()
    for r in read_seed("sport_aliases.csv"):
        if r["alias"].strip().lower() == want:
            return r["sport"].strip()
    return None


def find_pin(map_id):
    """The map's venue with this id (the popup prefills it), or None."""
    if not re.fullmatch(r"[0-9a-f]{10}", map_id or "") or not VENUES_JSON.exists():
        return None, []
    data = json.loads(VENUES_JSON.read_text(encoding="utf-8"))
    pin = next((v for v in data["venues"] if v["i"] == map_id), None)
    sports = [data["sports"][p[0]]["n"] for p in pin["p"]] if pin else []
    return pin, sports


def add_confirmation(key, user, method, seen, evidence):
    if any(r["venue_key"] == key and r["confirmed_by"].strip().lower() == user.lower() and r["method"] == method
           and r["confirmed_on"] == seen for r in read_seed("venue_confirmations.csv")):
        fail(f"@{user} already sent this {method} for this venue on {seen}.")
    append("venue_confirmations.csv", [key, user, method, seen, evidence])


def main():
    form = parse_form(os.environ["ISSUE_BODY"])
    num, user = os.environ["ISSUE_NUMBER"], os.environ["ISSUE_AUTHOR"]
    venue, city = clean(field(form, "Venue name"), 200), clean(field(form, "City"), 100)
    change, ltype = field(form, "What are you suggesting"), field(form, "If adding a way")
    source, price = clean(field(form, "Link to a public page"), 500), clean(field(form, "Price"), 200)
    seen, details = field(form, "Date you saw"), clean(field(form, "What did you see"))
    if not venue or not city or not details:
        fail("Venue, city and 'What did you see?' are required.")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", seen):
        fail("The date must be YYYY-MM-DD.")
    try:
        if date.fromisoformat(seen) > date.today():
            fail("The date is in the future.")
    except ValueError:
        fail("The date is not a real date.")
    if source and urlparse(source).scheme != "https":
        fail("The source link must be https.")
    evidence = f"Suggested in issue #{num} by @{user}, saw/checked {seen}: {details}" + (f" Source: {source}" if source else "")

    sport_text = clean(field(form, "Sport played here"), 60)
    sport = canonical_sport(sport_text) if sport_text else None
    if sport_text and not sport:
        fail(f"'{sport_text}' is not a sport we list; use the name the map's sport list shows.")
    reporting = change.lower().startswith("report a") and "sport" in change.lower().split("(")[0]   # tolerate wording edits ("Report a racket sport ...")
    confirming = change.startswith("Confirm")
    map_id = clean(field(form, "Map ID"), 20).lower()

    rows = read_seed("manual_venues.csv")
    key = next((r["venue_key"] for r in rows
                if r["venue_name"].strip().lower() == venue.lower() and r["city"].strip().lower() == city.lower()), None)
    pin, pin_sports = (None, []) if key else find_pin(map_id)
    if pin:   # this pin was reported before: add to that row instead of starting another
        key = next((r["venue_key"] for r in rows if f"map id {map_id}" in r["location_precision"]), None)

    if (reporting or confirming) and (key or pin):
        if confirming and not (source or "visited" in details.lower()):
            fail("A confirmation needs a public link, or say that you visited. To pass on what you saw or heard, pick 'Report a sport played here'.")
        method = "reported" if reporting else ("official" if source else "visited")
        known = {r["sport"] for r in rows if r["venue_key"] == key}
        if not sport and (reporting or not key):           # only a one-sport pin can leave the sport out
            if len(pin_sports) != 1:
                fail("Say which sport is played here (the 'Sport played here' field).")
            sport = pin_sports[0]
        if key and sport and sport not in known:          # a new sport at a venue the seeds already hold
            base = next(r for r in rows if r["venue_key"] == key)
            append("manual_venues.csv", [key, base["venue_name"], sport, base["city"], base["lat"], base["lon"], base["location_precision"],
                                         "", "unknown", "unknown", "", "", "unknown", "", "reported", seen, evidence, base["region"]])
            added = f"manual_venues.csv: {sport} at {key} (reported); "
        elif not key:                                      # first report on a pin from OSM or Overture
            key = f"report-{map_id}"
            access = "public" if pin["f"] & 2 else "members" if pin["f"] & 8 else "unknown"   # keep what the map already says
            append("manual_venues.csv", [key, pin["n"] or venue, sport, pin["c"] or city, pin["y"], pin["x"],
                                         f"pin: map id {map_id} (report on an existing map venue)", "", "unknown", "unknown", "", "",
                                         access, "", "reported", seen, evidence, pin["r"]])
            added = f"manual_venues.csv: {key} {sport} (reported, merges onto pin {map_id}); "
        else:
            added = ""
        add_confirmation(key, user, method, seen, evidence)
        print(f"{added}venue_confirmations.csv: {key} {method} by @{user}")
    elif change.startswith("Add a way") and key:
        if ltype not in LINK_TYPES or not source:
            fail("Adding a way to join needs a link type and an https link to a public page.")
        host = (urlparse(source).hostname or "other").removeprefix("www.")
        provider = host.split(".")[-2] if host.count(".") else host
        slug = re.sub(r"[^a-z0-9]+", "-", f"{key}-{LINK_TYPES[ltype]}-{num}".lower()).strip("-")
        append("venue_actions.csv", [slug, "manual", key, LINK_TYPES[ltype], f"{ltype} (suggested)", provider, source, price, "", "", evidence, seen])
        print(f"venue_actions.csv: {slug} for {key}")
    else:
        why = "venue not found in manual_venues; a reviewer must match it" if not key else "correction or closure"
        append("venue_leads.csv", [f"issue-{num}", venue, city, "", clean(f"{change}: {details}", 500), "issue", source, "new",
                                  f"Reviewer: check the source and place the change ({why})", date.today().isoformat(),
                                  f"Issue #{num} by @{user}; map id {field(form, 'Map ID')}"])
        print(f"venue_leads.csv: issue-{num}")


if __name__ == "__main__":
    main()
