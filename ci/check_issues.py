"""Check the repo's open issues before a reviewer acts on them (run at every twice-monthly sync: `make issues`).

For each open issue it says what is missing (fields, https public link, a real date, a map ID the map knows), whether the
seeds already handle it, whether it repeats another open issue, how long it has waited, and what adding the `approved`
label would write (issue-to-pr.yml). It only reads: nothing is commented, labelled, edited or closed. The `approved` label
stays the gate (ADR 0008).

Issues come from `gh issue list` (the GitHub CLI, logged in as you), or from --from-json FILE (same JSON, for tests).
Issue text is untrusted: it is parsed and printed, never executed.
"""
import argparse, csv, json, re, subprocess, sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from issue_to_pr import parse_form, field, LINK_TYPES  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "transform" / "seeds"
VENUES = ROOT / "app" / "data" / "venues.json"
STALE_DAYS = 14
FIELDS = "number,title,author,labels,createdAt,body,comments,url"
KINDS = {"venue-change": "change", "venue-confirmation": "confirm", "venue-report": "report", "event-report": "event"}
# Sources we may not store or that are not public pages (ADR 0005: no Google Places data; ADR 0007: no logged-in pages).
NOT_A_SOURCE = ("google.com/maps", "goo.gl/maps", "maps.app.goo.gl", "google.com/maps/d/")


def load_issues(path):
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    cmd = ["gh", "issue", "list", "--state", "open", "--limit", "200", "--json", FIELDS]
    return json.loads(subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True).stdout)


def seed_mentions():
    """Issue numbers the seeds already cite ('issue #12' in evidence, 'issue-12' as a lead id)."""
    found = {}
    for p in SEEDS.glob("*.csv"):
        for n in re.findall(r"issue[ -]#?(\d+)", p.read_text(encoding="utf-8", errors="replace"), re.I):
            found.setdefault(int(n), set()).add(p.name)
    return found


def manual_keys():
    with (SEEDS / "manual_venues.csv").open(newline="", encoding="utf-8") as f:
        return {(r["venue_name"].strip().lower(), r["city"].strip().lower()): r["venue_key"] for r in csv.DictReader(f)}


def check_link(url):
    if not url:
        return None
    url = url.split()[0]
    if urlparse(url).scheme != "https":
        return "link is not https"
    if any(s in url for s in NOT_A_SOURCE):
        return "link is a Google Maps page (not a public source we can cite; ADR 0005)"
    return None


def repo_owner():
    """The repo owner's login, from the origin remote (their own reports count as evidence, ADR 0007)."""
    try:
        url = subprocess.run(["git", "-C", str(ROOT), "remote", "get-url", "origin"], capture_output=True, text=True).stdout
    except OSError:
        return ""
    m = re.search(r"github\.com[:/]([^/]+)/", url)
    return m.group(1).lower() if m else ""


def check_event(issue, form, notes, age):
    """A tournament report (report-an-event.yml): needs an https organizer link and a real date; flags events already in the seeds."""
    name, link, start = field(form, "Event name"), field(form, "Link to the event page"), field(form, "Start date")
    need = [f"{label} missing" for label, val in (("event name", name), ("venue and city", field(form, "Venue and city"))) if not val]
    if (bad := check_link(link)) or not link:
        need.append(bad or "event page link missing")
    try:
        if date.fromisoformat(start) < date.today():
            need.append("event date is in the past")
    except (TypeError, ValueError):
        need.append("start date is not a real YYYY-MM-DD date")
    tid = re.search(r"TID=(\d+)", link or "")
    seeds = (SEEDS / "watch_events.csv").read_text(encoding="utf-8", errors="replace").lower()
    if tid and (f"tid={tid.group(1)}" in seeds):
        notes.append(f"R2 TID {tid.group(1)} is already in watch_events.csv: close the issue")
    elif name and name.strip().lower() in seeds:
        notes.append("an event with this name is already in watch_events.csv: close the issue if it is the same date")
    if tid:
        notes.append(f"R2 TID {tid.group(1)}: add a docs/r2_seen.csv row with your decision")
    if age > STALE_DAYS and not issue.get("comments"):
        notes.append(f"waiting {age} days with no reply")
    author = (issue.get("author") or {}).get("login", "?")
    nxt = ("ask the reporter: " + "; ".join(need)) if need else "by hand: add a watch_events.csv row (docs/tournament_refresh.md), then close the issue"
    return {"number": issue["number"], "title": issue["title"], "author": author, "kind": "event", "age": age, "map_id": "",
            "venue": "", "city": "", "need": need, "notes": notes, "next": nxt, "url": issue.get("url", "")}


def check(issue, venues, keys, mentions, today, owner=""):
    labels = {l["name"] for l in issue.get("labels", [])}
    kind = next((KINDS[l] for l in labels if l in KINDS), "other")
    form = parse_form(issue.get("body") or "")
    need, notes = [], []
    age = (today - date.fromisoformat(issue["createdAt"][:10])).days

    venue = field(form, "Venue name") or field(form, "Place name")
    city = field(form, "City") or field(form, "Address or cross streets")
    details = field(form, "What did you see") or field(form, "What is there")
    source = field(form, "Link to a public page") or field(form, "Link to a public source") or field(form, "Link to a source")
    seen = field(form, "Date you saw") or field(form, "When did you last see")
    change, ltype, map_id = field(form, "What are you suggesting"), field(form, "If adding a way"), field(form, "Map ID")

    if kind == "event":
        return check_event(issue, form, notes, age)
    if kind == "other":
        notes.append("not from an issue form: read it by hand")
    else:
        for name, val in (("venue name", venue), ("city", city), ("what they saw", details)):
            if not val:
                need.append(f"{name} missing")
        if kind != "report":
            try:
                if date.fromisoformat(seen) > today:
                    need.append("date is in the future")
            except (TypeError, ValueError):
                need.append("date is not a real YYYY-MM-DD date")
        # A pasted URL inside the free text counts as a source the reporter forgot to put in the link field.
        text_links = re.findall(r"https?://\S+", details or "")
        if (bad := check_link(source)):
            need.append(bad)
        elif not source:
            bad_text = [check_link(u) for u in text_links]
            if text_links and all(bad_text):
                need.append(f"no source link; the one in the text is unusable ({bad_text[0]})")
            elif text_links:
                notes.append("source link is in the text, not the link field: move it before approving")
            elif kind == "change" and change.startswith("Add a way"):
                need.append("adding a way to join needs an https public page")
            elif kind == "confirm" and "visited" not in (details or "").lower():
                need.append("a confirmation needs a public link or 'I visited'")
        if kind == "change" and change.startswith("Add a way") and ltype not in LINK_TYPES:
            need.append("pick the kind of link (open play, league, ...)")

    if map_id:
        v = venues.get(map_id)
        if not v:
            need.append(f"map ID {map_id} is not on the map (venue gone or ID edited)")
        elif venue and v.get("n", "").strip().lower() != venue.strip().lower():
            notes.append(f"map ID is '{v.get('n') or 'Unnamed courts'}', issue says '{venue}'")

    if issue["number"] in mentions:
        notes.append("already in seeds (" + ", ".join(sorted(mentions[issue["number"]])) + "): close the issue if the PR merged")
    if "approved" in labels:
        notes.append(f"approved: look for PR branch suggest/issue-{issue['number']}")
    if age > STALE_DAYS and not issue.get("comments") and "approved" not in labels:
        notes.append(f"waiting {age} days with no reply")

    author = (issue.get("author") or {}).get("login", "?")
    by_owner = bool(owner) and author.lower() == owner
    if by_owner and need:
        notes.append("filed by the owner: their own report is evidence (ADR 0007), so a missing public link is fine; "
                     "make the seed edit by hand with the issue as evidence")
        need = [n for n in need if "link" not in n and "visited" not in n]

    key = keys.get((venue.strip().lower(), city.strip().lower())) if venue and city else None
    if kind == "change":
        if change.startswith("Add a way") and key:
            would = f"venue_actions.csv link-out on {key}"
        elif change.startswith("Confirm") and key:
            would = f"venue_confirmations.csv row on {key}"
        else:
            would = "a lead in venue_leads.csv only; the fix itself is by hand (e.g. place_sport_overrides.csv for a wrong sport)"
        next_step = ("ask the reporter: " + "; ".join(need)) if need else (
            "by hand (owner report)" if by_owner and not source else f"ready: add `approved` -> {would}")
    elif kind in ("confirm", "report"):
        next_step = ("ask the reporter: " + "; ".join(need)) if need else "by hand: no automation for this form (manual_venues / venue_confirmations / leads)"
    else:
        next_step = "by hand"
    return {"number": issue["number"], "title": issue["title"], "author": author,
            "kind": kind, "age": age, "map_id": map_id, "venue": venue.strip().lower(), "city": city.strip().lower(),
            "need": need, "notes": notes, "next": next_step, "url": issue.get("url", "")}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--from-json", help="read issues from this file instead of calling gh")
    args = ap.parse_args()
    today = date.today()
    venues = {v["i"]: v for v in json.loads(VENUES.read_text(encoding="utf-8"))["venues"]}
    keys, mentions, owner = manual_keys(), seed_mentions(), repo_owner()
    rows = [check(i, venues, keys, mentions, today, owner) for i in load_issues(args.from_json)]

    # Duplicates: same map ID, or same venue + city, across open issues.
    for r in rows:
        dupes = [o["number"] for o in rows if o is not r and (
            (r["map_id"] and o["map_id"] == r["map_id"]) or (r["venue"] and (o["venue"], o["city"]) == (r["venue"], r["city"])))]
        if dupes:
            r["notes"].append("same venue as open issue(s) " + ", ".join(f"#{d}" for d in dupes))

    print(f"Open issues: {len(rows)} (checked {today})")
    for r in sorted(rows, key=lambda r: -r["age"]):
        print(f"\n#{r['number']} [{r['kind']}] {r['title']}  (@{r['author']}, {r['age']} days)")
        for n in r["need"]:
            print(f"  - needs: {n}")
        for n in r["notes"]:
            print(f"  - note: {n}")
        print(f"  -> {r['next']}")
    ready = sum(r["next"].startswith("ready") for r in rows)
    print(f"\nReady to approve: {ready}; need info: {sum(bool(r['need']) for r in rows)}; "
          f"waiting > {STALE_DAYS} days: {sum('waiting' in ' '.join(r['notes']) for r in rows)}")


if __name__ == "__main__":
    main()
