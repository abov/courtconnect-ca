"""Weekly audit digest and stalled-chain alert (ADR 0019 section 5; threat-model gap 4). No model, only `gh` and rules.

Looks at PRs merged in the last 7 days and prints a short markdown digest:
  1. every merged PR that touched a guarded path (workflows, ADRs, CLAUDE.md, ingestion/, models, macros, tests, app code, .env.example, SECURITY.md): the ADR 0019 R3 list;
  2. every merged PR where the required `dbt-build` check was not green at merge time (an `--admin` bypass shows up here);
  3. a reproducible random sample of the rest (10%, at least 5) for a person to spot-check against the page or diff;
  4. the alert: no scheduled-chain PR (`claude/tournaments-*` or `claude/refresh-*`) in 20 days.
`--post` opens one GitHub issue with the digest. Exit code 1 when the chain alert fires, so the workflow run fails and GitHub emails the owner.
Not built here: the second-model re-check of sampled facts (needs the page reader, ADR 0017). Offline test: ci/test_weekly_audit.py.
"""
import argparse, json, math, random, re, subprocess, sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAIN_MAX_DAYS = 20  # same number as ci/exception_queue.py (ADR 0019)
CHAIN_PREFIXES = ("claude/tournaments-", "claude/refresh-")
WINDOW_DAYS = 7
SAMPLE_FRACTION, SAMPLE_MIN = 0.10, 5
GUARDED_SHOWN = 20  # list length in the digest; the count in the heading is always the full one
REQUIRED_CHECK = "dbt-build"
# ADR 0019 "always R3" paths. Data files (seeds, app/data) are not guarded.
GUARDED = re.compile(
    r"^(\.github/|docs/decisions/|CLAUDE\.md$|SECURITY\.md$|\.env\.example$|ingestion/|ci/|transform/(models|macros|tests)/"
    r"|app/(?!data/)|Makefile$|requirements)"
)


def run_gh(args):
    out = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=120, cwd=ROOT)
    if out.returncode:
        raise RuntimeError(f"gh {' '.join(args[:3])} failed: {out.stderr.strip()[:200]}")
    return out.stdout


def parse_time(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def guarded_files(pr):
    return sorted(f["path"] for f in pr.get("files", []) if GUARDED.match(f["path"]))


def check_ok(pr):
    """True when the required check ended SUCCESS (or no check data came back, which is reported separately)."""
    for c in pr.get("statusCheckRollup") or []:
        if c.get("name") == REQUIRED_CHECK:
            return (c.get("conclusion") or "").upper() == "SUCCESS"
    return False


def pick_sample(prs, week_key):
    """Reproducible: the same week and the same PRs always give the same sample."""
    n = min(len(prs), max(SAMPLE_MIN, math.ceil(SAMPLE_FRACTION * len(prs))))
    return sorted(random.Random(week_key).sample(sorted(prs, key=lambda p: p["number"]), n), key=lambda p: p["number"])


def chain_status(chain_prs, now):
    """(days since the newest chain PR or None, alert text or None)."""
    ages = [(now - parse_time(p["createdAt"])).days for p in chain_prs if p["headRefName"].startswith(CHAIN_PREFIXES)]
    last = min(ages) if ages else None
    if last is None or last > CHAIN_MAX_DAYS:
        when = "ever" if last is None else f"in {last} days"
        return last, (f"No scheduled-chain PR (Tournaments/Refresh) {when}; limit is {CHAIN_MAX_DAYS} days. "
                      "Check https://claude.ai/code/routines and docs/cloud_routines.md.")
    return last, None


def line(pr, extra=""):
    return f"- #{pr['number']} {pr['title'][:70]}{extra}"


def build_digest(merged, chain_prs, now):
    since = now - timedelta(days=WINDOW_DAYS)
    week = [p for p in merged if p.get("mergedAt") and parse_time(p["mergedAt"]) >= since]
    iso = now.isocalendar()
    g_prs = [p for p in week if guarded_files(p)]
    red = [p for p in week if not check_ok(p)]
    rest = [p for p in week if p not in g_prs and p not in red]
    sample = pick_sample(rest, f"{iso[0]}-W{iso[1]:02d}") if rest else []
    last, alert = chain_status(chain_prs, now)
    out = [f"# Weekly audit {iso[0]}-W{iso[1]:02d}: {len(week)} PR(s) merged since {since:%Y-%m-%d}"]
    if alert:
        out += ["", f"## ALERT: {alert}"]
    else:
        out += ["", f"Scheduled chain: newest PR {last} day(s) ago (limit {CHAIN_MAX_DAYS})."]
    out += ["", f"## Merged without a green `{REQUIRED_CHECK}` ({len(red)})"] + ([line(p) for p in red] or ["- none"])
    out += ["", f"## Touched guarded paths, ADR 0019 R3 list ({len(g_prs)})"]
    for p in g_prs[:GUARDED_SHOWN]:
        files = guarded_files(p)
        out.append(line(p, f": {', '.join(files[:4])}" + (f" (+{len(files) - 4} more)" if len(files) > 4 else "")))
    if len(g_prs) > GUARDED_SHOWN:
        out.append(f"- ... and {len(g_prs) - GUARDED_SHOWN} more (`git log --name-only` for the rest)")
    if not g_prs:
        out.append("- none")
    out += ["", f"## Spot-check sample: {len(sample)} of {len(rest)} other PR(s)",
            "Open each, re-read its evidence link, and note any wrong fact; one wrong fact demotes that PR's class (ADR 0019 section 4)."]
    out += [line(p) for p in sample] or ["- none"]
    unknown = [p for p in week if p.get("filesKnown") is False]
    if unknown:
        out += ["", f"Files not found in the git history for {len(unknown)} PR(s) (not squash-merged?): " + ", ".join(f"#{p['number']}" for p in unknown)]
    out += ["", "_Rule-based digest (no model). The second-model re-check from ADR 0019 is not built._"]
    return "\n".join(out), alert


def files_by_pr(now):
    """PR number -> changed paths, read from squash-merge commits on origin/main (the API times out on 100+ PRs with files).
    Needs history for the window: the workflow fetches `--shallow-since`."""
    since = (now - timedelta(days=WINDOW_DAYS + 1)).strftime("%Y-%m-%d")
    out = subprocess.run(["git", "log", "origin/main", f"--since={since}", "--name-only", "--format=%x01%s"],
                         capture_output=True, text=True, timeout=120, cwd=ROOT)
    if out.returncode:
        raise RuntimeError(f"git log failed: {out.stderr.strip()[:200]}")
    files = {}
    for block in out.stdout.split("\x01")[1:]:
        subject, *paths = block.strip().splitlines()
        m = re.search(r"\(#(\d+)\)$", subject)
        if m:
            files[int(m.group(1))] = [{"path": x} for x in paths if x]
    return files


def merged_prs(now):
    """Merged PRs of the window, one gh call per day (a single call for 100+ PRs with check data returns a 502)."""
    prs = {}
    for d in range(WINDOW_DAYS + 1):
        day = (now - timedelta(days=d)).strftime("%Y-%m-%d")
        for p in json.loads(run_gh(["pr", "list", "--state", "merged", "--search", f"merged:{day}", "--limit", "100",
                                    "--json", "number,title,mergedAt,headRefName,statusCheckRollup"])):
            prs[p["number"]] = p
    files = files_by_pr(now)
    for n, p in prs.items():
        p["files"] = files.get(n, [])
        p["filesKnown"] = n in files
    return list(prs.values())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--post", action="store_true", help="open a GitHub issue with the digest (needs issues: write)")
    args = ap.parse_args()
    now = datetime.now(timezone.utc)
    merged = merged_prs(now)
    chain = json.loads(run_gh(["pr", "list", "--state", "all", "--limit", "150", "--json", "createdAt,headRefName"]))
    text, alert = build_digest(merged, chain, now)
    print(text)
    if args.post:
        title = ("ALERT: scheduled chain stalled. " if alert else "") + text.splitlines()[0].lstrip("# ")
        print(run_gh(["issue", "create", "--title", title, "--body", text]).strip())
    if alert:
        print(f"::error::{alert}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
