"""Print the exception queue: the short list of things that still need the owner (docs/self_service_plan.md).

Read-only. Reads outputs the project already writes, never changes anything, never comments or labels:
  - open PRs (stuck, red CI, conflicts, or an "owner decision" section in the body) and recent PR bodies, via `gh`
  - the newest scorecard line (failing SLAs, failing tests, old extract, old event checks, regression vs the line before)
  - docs/agent_log.csv (PRs still open, rejected, or escalated R3), the kill switch, the scheduled-chain watchdog signal
  - open GitHub issues waiting over 14 days or labelled needs-owner, via `gh`
  - seeds: venue_opening_status rows past the 90-day staleness window, open venue_leads that name an owner call
Anything routine (green PR, SLA met, fresh seed) is not listed. An empty queue prints "Nothing needs the owner."
`--no-gh` skips the GitHub parts (offline). Exit code is always 0: this is a report, not a gate.
"""
import argparse, csv, json, re, subprocess
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STALE_OPENING_DAYS = 90    # same window as assert_opening_status_fresh
EXTRACT_MAX_DAYS = 30      # 35-day freshness SLA: warn before it breaches
EVENT_CHECK_MAX_DAYS = 14  # "oldest upcoming-event check" SLA
PR_WAIT_HOURS = 24
ISSUE_WAIT_DAYS = 14
CHAIN_MAX_DAYS = 20        # ADR 0019: alert if no scheduled-chain PR in 20 days
OWNER_CALL = re.compile(r"owner (call|decision|ruling)\b|ask the owner|owner to (give|decide|confirm)", re.I)
DECISION_HEAD = re.compile(r"needs? owner decisions?", re.I)


def gh_json(args):
    try:
        out = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=60, cwd=ROOT)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode:
        return None
    try:
        return json.loads(out.stdout)
    except ValueError:
        return None


def read_csv(path):
    p = ROOT / path
    if not p.exists():
        return []
    with p.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def num(row, col):
    try:
        return float(row.get(col, ""))
    except (TypeError, ValueError):
        return None


def days_since(iso, today):
    try:
        return (today - date.fromisoformat(iso[:10])).days
    except ValueError:
        return None


def decision_lines(body):
    """Lines under a 'needs owner decision' heading or bullet in a PR body (until a blank line or next heading)."""
    out, on = [], False
    for line in (body or "").splitlines():
        s = line.strip()
        if DECISION_HEAD.search(s):
            on = True
            rest = re.sub(r"^[#*\-\s]*[^:]*needs? owner decisions?[^:]*:?", "", s, flags=re.I).strip(" *-:")
            if rest:
                out.append(rest)
            continue
        if on:
            if not s or s.startswith("#"):
                on = False
            else:
                out.append(s.lstrip("-* ").strip())
    return [x for x in out if x and x.lower() not in ("none", "nothing", "n/a")]


def scorecard_items():
    rows = read_csv("docs/data_quality_trend.csv")
    if not rows:
        return []
    new, items = rows[-1], []
    met, total = num(new, "sla_met"), num(new, "sla_total")
    if met is not None and total is not None and met < total:
        items.append(f"{int(total - met)} of {int(total)} SLAs failing on {new['date']} (`make quality`; `docs/data_quality.md` names them)")
    if (num(new, "tests_fail") or 0) > 0:
        items.append(f"{int(num(new, 'tests_fail'))} dbt tests failing in the {new['date']} scorecard line")
    age = num(new, "extract_age_days")
    if age is not None and age > EXTRACT_MAX_DAYS:
        items.append(f"OSM extract is {int(age)} days old; the 35-day freshness SLA breaches soon (an extract needs the owner's OK)")
    ev = num(new, "events_oldest_check_days")
    if ev is not None and ev > EVENT_CHECK_MAX_DAYS:
        items.append(f"oldest upcoming-event check is {int(ev)} days old (SLA {EVENT_CHECK_MAX_DAYS}); re-read or run the tournament parts")
    if len(rows) > 1:
        old = rows[-2]
        v0, v1 = num(old, "venues"), num(new, "venues")
        if v0 and v1 is not None and (v0 - v1) / v0 * 100 > 1.0:
            items.append(f"venues fell {v0:.0f} -> {v1:.0f} (> 1%) between {old['date']} and {new['date']}")
        s0, s1 = num(old, "seen_35d_pct"), num(new, "seen_35d_pct")
        if s0 is not None and s1 is not None and s1 < s0:
            items.append(f"'seen in 35 days' fell {s0}% -> {s1}%")
    return items


def pr_state(number, use_gh):
    if not use_gh:
        return "UNKNOWN"
    data = gh_json(["pr", "view", str(number), "--json", "state"])
    return (data or {}).get("state", "UNKNOWN")


def agent_log_items(use_gh=True):
    items = []
    for r in read_csv("docs/agent_log.csv"):
        if r.get("outcome") == "rejected":
            items.append(f"agent PR #{r['pr']} ({r['date']}) was rejected: demote its class to stage 0 until re-enabled (ADR 0019)")
        elif r.get("class") == "R3" and r.get("outcome") == "open" and pr_state(r["pr"], use_gh) in ("OPEN", "UNKNOWN"):
            items.append(f"agent PR #{r['pr']} ({r['date']}) is R3 (escalated) and not merged or closed")
    kill = (ROOT / "docs" / "agents_enabled.txt")
    first = kill.read_text(encoding="utf-8").splitlines()[0].strip() if kill.exists() and kill.read_text(encoding="utf-8").strip() else ""
    if first != "true":
        items.append(f"kill switch: docs/agents_enabled.txt says '{first or 'missing'}', cloud agents will stop at preflight")
    return items


def seed_items(today):
    items = []
    for r in read_csv("transform/seeds/venue_opening_status.csv"):
        d = days_since(r.get("verified_on", ""), today)
        if d is not None and d > STALE_OPENING_DAYS:
            items.append(f"opening status '{r['venue_key']}' last verified {d} days ago: open, still coming, or delete the row")
    for r in read_csv("transform/seeds/venue_leads.csv"):
        if r.get("status") in ("resolved", "rejected"):
            continue
        text = (r.get("next_step", "") + " " + r.get("notes", ""))
        # needs_location / needs_visit are agent research work (a page read, a geocode), not owner calls
        if OWNER_CALL.search(text):
            items.append(f"lead `{r['lead_id']}` ({r.get('status')}): {r.get('next_step', '')[:110]}")
    return items


def gh_items(today):
    items = []
    prs = gh_json(["pr", "list", "--state", "open", "--limit", "50",
                   "--json", "number,title,createdAt,isDraft,mergeable,statusCheckRollup,body,headRefName"])
    if prs is None:
        return ["GitHub not reachable (`gh` missing or not logged in): PRs, issues and the chain watchdog were not checked"]
    for p in prs:
        age_h = (datetime.now(timezone.utc) - datetime.fromisoformat(p["createdAt"].replace("Z", "+00:00"))).total_seconds() / 3600
        checks = p.get("statusCheckRollup") or []
        failed = [c.get("name") for c in checks if (c.get("conclusion") or "").upper() in ("FAILURE", "TIMED_OUT", "CANCELLED")]
        why = []
        if failed:
            why.append("red: " + ", ".join(sorted(set(filter(None, failed)))))
        if p.get("mergeable") == "CONFLICTING":
            why.append("merge conflict")
        if age_h > PR_WAIT_HOURS and not p.get("isDraft"):
            why.append(f"open {age_h / 24:.1f} days")
        if why:
            items.append(f"PR #{p['number']} {p['title'][:60]}: {'; '.join(why)}")
        for line in decision_lines(p.get("body")):
            items.append(f"PR #{p['number']} owner decision: {line[:140]}")
    since = gh_json(["pr", "list", "--state", "merged", "--limit", "30", "--json", "number,mergedAt,body,title"]) or []
    for p in since:
        d = days_since(p.get("mergedAt", ""), today)
        if d is not None and d <= 14:
            for line in decision_lines(p.get("body")):
                items.append(f"merged PR #{p['number']} owner decision: {line[:140]}")
    issues = gh_json(["issue", "list", "--state", "open", "--limit", "50", "--json", "number,title,createdAt,labels"]) or []
    for i in issues:
        labels = {l["name"] for l in i.get("labels", [])}
        d = days_since(i["createdAt"], today)
        if "needs-owner" in labels or (d is not None and d > ISSUE_WAIT_DAYS and "approved" not in labels):
            items.append(f"issue #{i['number']} {i['title'][:60]}: waiting {d} days (`make issues` says what is missing)")
    chain = gh_json(["pr", "list", "--state", "all", "--limit", "150", "--json", "title,createdAt,headRefName"]) or []
    chain = [p for p in chain if p["headRefName"].startswith(("claude/tournaments-", "claude/refresh-"))]
    last = min((days_since(p["createdAt"], today) for p in chain if days_since(p["createdAt"], today) is not None), default=None)
    if last is None or last > CHAIN_MAX_DAYS:
        items.append(f"no scheduled-chain PR (Tournaments/Refresh) in {CHAIN_MAX_DAYS}+ days: check https://claude.ai/code/routines")
    return items


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-gh", action="store_true", help="skip the GitHub parts (offline)")
    args = ap.parse_args()
    today = date.today()
    sections = [
        ("PRs, issues, schedule", [] if args.no_gh else gh_items(today)),
        ("Scorecard", scorecard_items()),
        ("Agents", agent_log_items(not args.no_gh)),
        ("Seeds (owner calls, stale rows)", seed_items(today)),
    ]
    total = sum(len(x) for _, x in sections)
    print(f"# Exception queue {today}: {total} item(s)")
    if not total:
        print("Nothing needs the owner.")
    for title, items in sections:
        if items:
            print(f"\n## {title} ({len(items)})")
            for it in items:
                print(f"- {it}")


if __name__ == "__main__":
    main()
