"""Delivery and workflow metrics for the project (docs/ops_metrics.md): what the pipeline's own tools do not record.

    python ingestion/ops_metrics.py                    (or: make ops-metrics ARGS="--days 7 --only prs,runs")

Read-only, prints a short report, writes nothing (so there is no generated file to go stale). Sections (--only, comma list):
  prs     merged PRs per day, PRs carrying merge/rebase/regenerate-venues.json commits (the conflict signal), time open, venues.json collisions
  runs    GitHub Actions per workflow: runs, failures, cancellations, median/p90/max duration, and the slowest steps of the latest ci and pages runs
  build   slowest dbt models of the last local dbt invocation (transform/target/run_results.json)
  tokens  Claude Code usage from this machine's own session logs (~/.claude/projects/*courtconnect*): tokens per day, heaviest sessions,
          and which tools put the most text into context. Reads only counts and tool names, never prints prompts or file contents.
Needs `gh` logged in for prs and runs. GitHub does not record merge conflicts, so the conflict signal is inferred from commit messages.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import statistics
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# A commit that exists only because main moved: a merge of main, a rebase, a conflict fix, or a regenerated export.
CONFLICT_RE = re.compile(r"^merge (branch|remote|main|origin)|rebase|conflict|(regenerate|rebuild|re-?run)\W+(the\W+)?venues", re.I)
GENERATED = "app/data/venues.json"


def ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def day(d: datetime) -> str:
    return d.astimezone().strftime("%Y-%m-%d")


def mins(a: str, b: str) -> float:
    return (ts(b) - ts(a)).total_seconds() / 60


def p90(xs: list[float]) -> float:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(len(xs) * 0.9))]


def gh(*args: str):
    r = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
    if r.returncode:
        sys.exit(f"gh failed ({' '.join(args[:2])}): {r.stderr.strip()}")
    return json.loads(r.stdout)


def section(title: str) -> None:
    print(f"\n== {title} ==")


def prs(cutoff: datetime) -> None:
    section("Merged PRs per day (conflict signal inferred from commit messages)")
    # The bulk query cannot include commits (GitHub's GraphQL node limit), so commits come one PR at a time.
    rows = [p for p in gh("pr", "list", "--state", "merged", "--limit", "100",
                          "--json", "number,createdAt,mergedAt,files") if ts(p["mergedAt"]) >= cutoff]
    if not rows:
        print("no merged PRs in range")
        return
    for p in rows:
        p["commits"] = gh("pr", "view", str(p["number"]), "--json", "commits")["commits"]
    per = collections.defaultdict(list)
    for p in rows:
        per[day(ts(p["mergedAt"]))].append(p)
    print(f"{'day':<11}{'merged':>7}{'w/ conflict commits':>21}{'extra commits':>15}{'touch venues.json':>19}{'median open (min)':>19}")
    for d in sorted(per):
        ps = per[d]
        flagged = [p for p in ps if any(CONFLICT_RE.search(c["messageHeadline"]) for c in p["commits"])]
        extra = sum(sum(bool(CONFLICT_RE.search(c["messageHeadline"])) for c in p["commits"]) for p in ps)
        gen = sum(any(f["path"] == GENERATED for f in p["files"]) for p in ps)
        open_min = statistics.median(mins(p["createdAt"], p["mergedAt"]) for p in ps)
        print(f"{d:<11}{len(ps):>7}{len(flagged):>21}{extra:>15}{gen:>19}{open_min:>19.0f}")
    flagged_all = [p for p in rows if any(CONFLICT_RE.search(c["messageHeadline"]) for c in p["commits"])]
    print(f"total {len(rows)} PRs, {len(flagged_all)} ({100 * len(flagged_all) // len(rows)}%) needed a merge/rebase/regenerate commit; "
          f"{statistics.mean(len(p['commits']) for p in rows):.1f} commits per PR on average")
    if flagged_all:
        print("most affected: " + ", ".join(f"#{p['number']}" for p in sorted(
            flagged_all, key=lambda p: -sum(bool(CONFLICT_RE.search(c['messageHeadline'])) for c in p['commits']))[:5]))


def runs(cutoff: datetime) -> None:
    section("GitHub Actions per workflow (duration = started to last update, minutes)")
    all_runs = [r for r in gh("run", "list", "--limit", "500", "--json",
                              "databaseId,workflowName,conclusion,event,startedAt,updatedAt,headBranch") if ts(r["startedAt"]) >= cutoff]
    by = collections.defaultdict(list)
    for r in all_runs:
        by[r["workflowName"]].append(r)
    print(f"{'workflow':<22}{'runs':>6}{'failed':>8}{'cancelled':>11}{'median':>8}{'p90':>7}{'max':>7}")
    for name, rs in sorted(by.items(), key=lambda kv: -len(kv[1])):
        done = [mins(r["startedAt"], r["updatedAt"]) for r in rs if r["conclusion"] in ("success", "failure")]
        fail = sum(r["conclusion"] == "failure" for r in rs)
        canc = sum(r["conclusion"] == "cancelled" for r in rs)
        d = f"{statistics.median(done):>8.1f}{p90(done):>7.1f}{max(done):>7.1f}" if done else f"{'-':>8}{'-':>7}{'-':>7}"
        print(f"{name:<22}{len(rs):>6}{fail:>8}{canc:>11}{d}")
    fails = collections.Counter(day(ts(r["startedAt"])) for r in all_runs if r["conclusion"] == "failure")
    print("failed runs per day: " + (", ".join(f"{k} {v}" for k, v in sorted(fails.items())) or "none"))
    for wf in ("ci", "pages"):
        ok = next((r for r in all_runs if r["workflowName"] == wf and r["conclusion"] == "success"), None)
        if not ok:
            continue
        jobs = gh("run", "view", str(ok["databaseId"]), "--json", "jobs")["jobs"]
        steps = [(mins(s["startedAt"], s["completedAt"]), j["name"], s["name"]) for j in jobs for s in j["steps"]
                 if s.get("startedAt") and s.get("completedAt")]
        print(f"slowest steps, latest successful '{wf}' run ({ok['databaseId']}):")
        for m, j, s in sorted(steps, reverse=True)[:6]:
            print(f"  {m:>5.1f} min  {j} / {s}")


def build() -> None:
    section("Local dbt: slowest models of the last invocation")
    f = ROOT / "transform" / "target" / "run_results.json"
    if not f.exists():
        print("no transform/target/run_results.json here (run dbt build; a new worktree has none)")
        return
    rr = json.loads(f.read_text(encoding="utf-8"))
    print(f"invocation {rr['metadata']['generated_at'][:19]}Z, {len(rr['results'])} nodes, {rr['elapsed_time']:.0f}s total "
          f"(a selective build overwrites this file, so it shows the last run only)")
    for r in sorted(rr["results"], key=lambda r: -r["execution_time"])[:8]:
        print(f"  {r['execution_time']:>6.1f}s  {r['status']:<8}{r['unique_id']}")


def tokens(cutoff: datetime) -> None:
    section("Claude Code usage on this machine (session logs; counts only)")
    base = Path.home() / ".claude" / "projects"
    files = [f for d in base.glob("*courtconnect*") for f in d.rglob("*.jsonl") if datetime.fromtimestamp(f.stat().st_mtime, timezone.utc) >= cutoff]
    if not files:
        print("no session logs found")
        return
    seen: set[str] = set()
    per_day = collections.defaultdict(lambda: collections.Counter())
    sess = collections.defaultdict(lambda: collections.Counter())
    names: dict[str, str] = {}
    tool_name: dict[str, str] = {}
    tool_chars = collections.Counter()
    tool_calls = collections.Counter()

    def label(name: str, inp: dict) -> str:
        if name != "Bash":
            return name
        cmd = (inp.get("command") or "").strip()
        m = re.search(r"(ingestion/\w+\.py|ci/\w+\.py|dbt|gh|git|pytest|node|make)\b", cmd)
        return "Bash:" + (m.group(1) if m else cmd.split(" ")[0][:14])

    for f in files:
        proj = f.relative_to(base).parts[0].split("worktrees-")[-1][:34]
        for line in f.open(encoding="utf-8", errors="replace"):
            try:
                o = json.loads(line)
            except ValueError:
                continue
            msg = o.get("message")
            if not isinstance(msg, dict) or not o.get("timestamp"):
                continue
            when = ts(o["timestamp"])
            content = msg.get("content")
            if o.get("type") == "assistant":
                for b in content if isinstance(content, list) else []:
                    if b.get("type") == "tool_use":
                        tool_name[b["id"]] = label(b["name"], b.get("input") or {})
                u, mid = msg.get("usage"), msg.get("id")
                if when < cutoff or not u or not mid or mid in seen:
                    continue
                seen.add(mid)
                ctx = u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
                for bucket in (per_day[day(when)], sess[o.get("sessionId", f.stem)]):
                    bucket["turns"] += 1
                    bucket["out"] += u.get("output_tokens", 0)
                    bucket["fresh"] += u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
                    bucket["cache_read"] += u.get("cache_read_input_tokens", 0)
                s = sess[o.get("sessionId", f.stem)]
                s["peak"] = max(s["peak"], ctx)
                names[o.get("sessionId", f.stem)] = proj
            elif o.get("type") == "user" and when >= cutoff and isinstance(content, list):
                for b in content:
                    if b.get("type") == "tool_result" and b.get("tool_use_id") in tool_name:
                        c = b.get("content")
                        n = len(c) if isinstance(c, str) else sum(len(x.get("text", "")) for x in c if isinstance(x, dict))
                        tool_chars[tool_name[b["tool_use_id"]]] += n
                        tool_calls[tool_name[b["tool_use_id"]]] += 1
    print("tokens per day (k): fresh = new input written to cache, cache_read = re-read context each turn, out = generated")
    print(f"{'day':<11}{'turns':>7}{'fresh':>9}{'cache_read':>12}{'out':>8}")
    for d in sorted(per_day):
        c = per_day[d]
        print(f"{d:<11}{c['turns']:>7}{c['fresh'] / 1e3:>9.0f}{c['cache_read'] / 1e3:>12.0f}{c['out'] / 1e3:>8.0f}")
    print("heaviest sessions (by fresh + output; peak = largest context sent in one turn, the 'start a fresh session' signal):")
    for sid, c in sorted(sess.items(), key=lambda kv: -(kv[1]["fresh"] + kv[1]["out"]))[:6]:
        print(f"  {sid[:8]}  {names.get(sid, '?'):<35}{c['turns']:>5} turns  fresh {c['fresh'] / 1e3:>6.0f}k  out {c['out'] / 1e3:>5.0f}k  peak {c['peak'] / 1e3:>5.0f}k")
    print("tools that put the most text into context (characters returned, calls):")
    for t, n in tool_chars.most_common(8):
        print(f"  {n / 1e3:>8.0f}k chars  {tool_calls[t]:>5} calls  {t}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--only", default="prs,runs,build,tokens")
    a = ap.parse_args()
    cutoff = datetime.now(timezone.utc) - timedelta(days=a.days)
    want = set(a.only.split(","))
    print(f"ops metrics, last {a.days} days (days shown in local time)")
    if "prs" in want:
        prs(cutoff)
    if "runs" in want:
        runs(cutoff)
    if "build" in want:
        build()
    if "tokens" in want:
        tokens(cutoff)


if __name__ == "__main__":
    main()
