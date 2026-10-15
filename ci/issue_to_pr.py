"""Turn an approved "Suggest a change" issue into a seed edit (run by .github/workflows/issue-to-pr.yml).

Reads the issue form body from $ISSUE_BODY and writes ONE row:
  - a link-out to venue_actions.csv, or a confirmation to venue_confirmations.csv, when the venue name + city match a row in
    manual_venues.csv (the only venues the seeds can address by key);
  - otherwise a lead in venue_leads.csv, so a reviewer can place it. Leads are not shown on the map.
The issue text is untrusted: it is only ever written through the csv module, URLs must be https, and nothing is executed.
Prints a one-line summary on success; exits 1 with a reason on bad input.
"""
import csv, os, re, sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

SEEDS = Path(__file__).resolve().parents[1] / "transform" / "seeds"
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
    needs_newline = not path.read_bytes().endswith(b"\n")
    with path.open("a", newline="", encoding="utf-8") as f:
        if needs_newline:
            f.write("\n")
        csv.writer(f, lineterminator="\n").writerow(row)


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

    key = None
    with (SEEDS / "manual_venues.csv").open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["venue_name"].strip().lower() == venue.lower() and r["city"].strip().lower() == city.lower():
                key = r["venue_key"]
                break

    if change.startswith("Add a way") and key:
        if ltype not in LINK_TYPES or not source:
            fail("Adding a way to join needs a link type and an https link to a public page.")
        host = (urlparse(source).hostname or "other").removeprefix("www.")
        provider = host.split(".")[-2] if host.count(".") else host
        slug = re.sub(r"[^a-z0-9]+", "-", f"{key}-{LINK_TYPES[ltype]}-{num}".lower()).strip("-")
        append("venue_actions.csv", [slug, "manual", key, LINK_TYPES[ltype], f"{ltype} (suggested)", provider, source, price, "", "", evidence, seen])
        print(f"venue_actions.csv: {slug} for {key}")
    elif change.startswith("Confirm") and key:
        if not (source or "visited" in details.lower()):
            fail("A confirmation needs a public link, or say that you visited.")
        method = "official" if source else "visited"
        append("venue_confirmations.csv", [key, user, method, seen, evidence])
        print(f"venue_confirmations.csv: {key} {method} by @{user}")
    else:
        why = "venue not found in manual_venues; a reviewer must match it" if not key else "correction or closure"
        append("venue_leads.csv", [f"issue-{num}", venue, city, "", clean(f"{change}: {details}", 500), "issue", source, "new",
                                  f"Reviewer: check the source and place the change ({why})", date.today().isoformat(),
                                  f"Issue #{num} by @{user}; map id {field(form, 'Map ID')}"])
        print(f"venue_leads.csv: issue-{num}")


if __name__ == "__main__":
    main()
