"""Feedback ledger: every piece of outside feedback (issues, comments, form reports, messages) in one CSV, so handled items stay visible.

`python ci/feedback_log.py` syncs all GitHub issues (open AND closed) into docs/feedback_log.csv, then prints what is open, what
is waiting on the reporter, what was resolved recently and any new comment on an issue that was already closed. It only writes the
CSV (never comments, labels or closes anything on GitHub). Fields a person edited (kind, summary, status, resolution) are kept; the
sync only fills blanks and moves `open` -> `done`/`closed` when the issue closes.

Feedback that is not a GitHub issue (a message, a call, a form report, analytics) goes in with --add:
  python ci/feedback_log.py --add --channel message --reporter friend-padel --kind bug --summary "Map is slow on my phone"
Issue text is untrusted: it is parsed and printed, never executed.
"""
import argparse, csv, json, re, statistics, subprocess, sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "docs" / "feedback_log.csv"
COLS = ["id", "received_on", "channel", "reporter", "kind", "summary", "status", "resolved_on", "resolution", "link"]
FIELDS = "number,title,author,labels,createdAt,closedAt,state,comments,url,closedByPullRequestsReferences"
KINDS = {"venue-change": "wrong-data", "venue-confirmation": "wrong-data", "venue-report": "missing-place", "event-report": "missing-place"}
STATUSES = ("open", "waiting-on-reporter", "done", "closed", "declined")
OPEN = ("open", "waiting-on-reporter")
RECENT_DAYS = 30


def load_issues(path):
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    cmd = ["gh", "issue", "list", "--state", "all", "--limit", "500", "--json", FIELDS]
    return json.loads(subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True).stdout)


def read_log(path=None):
    path = path or LOG
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_log(rows, path=None):
    with (path or LOG).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["received_on"], r["id"])))


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()[:140]


def issue_row(i):
    labels = {l["name"] for l in i.get("labels", [])}
    prs = i.get("closedByPullRequestsReferences") or []
    closed = i.get("state", "").upper() == "CLOSED"
    resolved = (i.get("closedAt") or "")[:10]
    return {"id": f"gh-{i['number']}", "received_on": i["createdAt"][:10], "channel": "github-issue",
            "reporter": (i.get("author") or {}).get("login", "?"),
            "kind": next((KINDS[l] for l in sorted(labels) if l in KINDS), "other"), "summary": clean(i["title"]),
            "status": ("done" if prs else "closed") if closed else "open", "resolved_on": resolved if closed else "",
            "resolution": f"PR #{prs[0]['number']}" if prs else "", "link": i.get("url", "")}


def sync(rows, issues, today):
    """Merge GitHub issues into the ledger. Returns (added, closed_now, reopened, late_comments)."""
    by_id = {r["id"]: r for r in rows}
    added, closed_now, reopened, late = [], [], [], []
    for i in issues:
        new = issue_row(i)
        old = by_id.get(new["id"])
        if not old:
            rows.append(new)
            by_id[new["id"]] = new
            added.append(new["id"])
            old = new
        elif old["status"] in OPEN and new["status"] not in OPEN:
            old["status"], old["resolved_on"] = new["status"], new["resolved_on"]
            closed_now.append(old["id"])
        elif old["status"] not in OPEN and new["status"] == "open" and old["channel"] == "github-issue":
            old["status"], old["resolved_on"] = "open", ""
            reopened.append(old["id"])
        for k in ("resolution", "reporter", "link", "kind", "summary"):
            if not old[k]:
                old[k] = new[k]
        closed_at = (i.get("closedAt") or "")
        for c in i.get("comments") or []:      # a reply after the issue closed is feedback on handled work
            if closed_at and (c.get("createdAt") or "") > closed_at and old["status"] not in OPEN:
                late.append(old["id"])
                break
    return added, closed_now, reopened, late


def add_row(rows, channel, reporter, kind, summary, link, today):
    n = sum(r["id"].startswith(f"{channel}-{today:%Y%m%d}") for r in rows) + 1
    rows.append({"id": f"{channel}-{today:%Y%m%d}-{n}", "received_on": today.isoformat(), "channel": channel,
                 "reporter": reporter, "kind": kind, "summary": clean(summary), "status": "open",
                 "resolved_on": "", "resolution": "", "link": link})
    return rows[-1]["id"]


def report(rows, today, notes):
    age = lambda r: (today - date.fromisoformat(r["received_on"])).days
    open_rows = sorted((r for r in rows if r["status"] in OPEN), key=lambda r: -age(r))
    print(f"Feedback log: {len(rows)} items, {len(open_rows)} open (checked {today})")
    for label, ids in notes:
        if ids:
            print(f"  {label}: {', '.join(ids)}")
    for r in open_rows:
        print(f"\n{r['id']} [{r['channel']}/{r['kind']}] {r['summary']}  ({r['reporter']}, {age(r)} days, {r['status']})")
        if r["link"]:
            print(f"  {r['link']}")
    done = [r for r in rows if r["status"] not in OPEN and r["resolved_on"]]
    days = [(date.fromisoformat(r["resolved_on"]) - date.fromisoformat(r["received_on"])).days for r in done]
    recent = [r for r in done if (today - date.fromisoformat(r["resolved_on"])).days <= RECENT_DAYS]
    print(f"\nHandled: {len(done)} total, {len(recent)} in the last {RECENT_DAYS} days"
          + (f", median {statistics.median(days):g} days to resolve" if days else ""))
    by = {}
    for r in rows:
        by[r["channel"]] = by.get(r["channel"], 0) + 1
    print("By channel: " + ", ".join(f"{k} {v}" for k, v in sorted(by.items())))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--from-json", help="read issues from this file instead of calling gh")
    ap.add_argument("--no-sync", action="store_true", help="skip GitHub; just report on the CSV")
    ap.add_argument("--add", action="store_true", help="log feedback that is not a GitHub issue")
    ap.add_argument("--channel", default="message", choices=["message", "call", "form", "analytics", "comment"])
    ap.add_argument("--reporter", default="", help="a tag or login; never an email or phone number")
    ap.add_argument("--kind", default="other")
    ap.add_argument("--summary", default="")
    ap.add_argument("--link", default="")
    args = ap.parse_args()
    today, rows = date.today(), read_log()
    if args.add:
        if not args.summary:
            sys.exit("--add needs --summary")
        if re.search(r"@\S+\.\S+|\+?\d[\d\s().-]{8,}", args.reporter + args.summary):
            sys.exit("looks like it has an email or phone number: leave personal contact out of the log")
        print("added", add_row(rows, args.channel, args.reporter, args.kind, args.summary, args.link, today))
        write_log(rows)
        return
    notes = []
    if not args.no_sync:
        added, closed_now, reopened, late = sync(rows, load_issues(args.from_json), today)
        write_log(rows)
        notes = [("new", added), ("closed since last sync", closed_now), ("reopened", reopened),
                 ("new comment after close (read it)", late)]
    report(rows, today, notes)


if __name__ == "__main__":
    main()
