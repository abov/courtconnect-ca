"""Write app/data/build_stats.json: the measured numbers shown on app/how-its-built.html.

    python ingestion/build_stats.py            (or: make stats)   run after `make quality`, in the refresh PR
    python ingestion/build_stats.py --keep-gold   Pages deploy: rebuild everything but keep the last scored gold set
    python ingestion/build_stats.py --check    CI: the file is well formed and dated like the newest scorecard row
    python ingestion/build_stats.py --docs     (make stats) also rewrites the numbers blocks in docs/case_study.md and docs/talk_outline.md

Nothing is typed in by hand. Every number comes from a file or check that already exists:
  the map     app/data/venues.json meta (venues, sports, export size): always the numbers the live map shows
  scorecard   last row of docs/data_quality_trend.csv (real-name share, service levels, dbt tests), dated `scorecard_as_of`
  structure   file counts in transform/, ci/ and docs/decisions/
  gold set    ingestion/eval_match_gold.py against the local DuckDB; when the database is missing or locked the
              previous values in this file are kept (CI never builds the full warehouse)
  Overture    docs/planet_scale_benchmark.json (bytes the real extracts fetched vs the size of the themes)
  history     every row of docs/data_quality_trend.csv, for app/run-history.html
  agent_runs  every row of docs/agent_log.csv (re-run this script after the refresh agent appends its log row)
  ask         the Ask box test set (`node chatbot/test_ask.js`: questions passed of total; the previous values are kept when Node is
              missing) and its last 7 days of use from docs/usage_events.csv: questions asked and how many it could not answer
              (a refuse, support or gear reply, or a search with no results). The questions themselves stay local (`make ask-feedback`).
Nothing here goes stale on the live site: .github/workflows/pages.yml re-runs this script on every deploy (and daily), before the
dashboard export, so the file the pages read is rebuilt from the current repo; the committed copy is only the offline fallback.
--check fails when the committed history/agent rows differ from their CSVs or `scorecard_as_of` is not the newest scorecard row.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ingestion"))
OUT = ROOT / "app" / "data" / "build_stats.json"
TREND = ROOT / "docs" / "data_quality_trend.csv"
VENUES = ROOT / "app" / "data" / "venues.json"
BENCH = ROOT / "docs" / "planet_scale_benchmark.json"
KEYS = ["as_of", "scorecard_as_of", "export_mb", "adrs_superseded", "venues", "sports_with_venues", "sports_total", "named_pct", "sla_met", "sla_total", "tests_pass", "tests_fail",
        "models", "seeds", "custom_tests", "adrs", "ci_checks", "gold", "overture", "history", "agent_runs", "ask"]
AGENT_LOG = ROOT / "docs" / "agent_log.csv"
USAGE_EVENTS = ROOT / "docs" / "usage_events.csv"
ASK_MISS_KINDS = {"refuse", "support", "gear"}   # app/ask.js MISS_KINDS; a search with no results is counted by its own ask-empty event
HISTORY_INT = ["venues", "sports_with_venues", "events_upcoming", "actions_current", "extract_age_days", "sla_met", "sla_total",
               "tests_pass", "tests_warn", "tests_fail"]
HISTORY_FLOAT = ["named_pct", "sites_dead_pct", "seen_35d_pct"]  # seen_35d_pct is blank on the first row: kept as null


def last_trend_row() -> dict:
    rows = list(csv.DictReader(TREND.open(encoding="utf-8")))
    return rows[-1]


def history_rows() -> list[dict]:
    """Every scorecard row, numbers as numbers (blank = None), oldest first."""
    out = []
    for r in csv.DictReader(TREND.open(encoding="utf-8")):
        row = {"date": r["date"]}
        row.update({k: int(r[k]) for k in HISTORY_INT})
        row.update({k: (float(r[k]) if r[k] != "" else None) for k in HISTORY_FLOAT})
        out.append(row)
    return out


def agent_run_rows() -> list[dict]:
    rows = list(csv.DictReader(AGENT_LOG.open(encoding="utf-8")))
    return [{**r, "pr": int(r["pr"]) if r["pr"].isdigit() else None, "est_cost_usd": float(r["est_cost_usd"])} for r in rows]


def gold_numbers(previous: dict | None) -> dict:
    """Pairs, wrong merges and missed merges from the gold set; the old values when the warehouse cannot be read."""
    import eval_match_gold as gold

    rows = gold.load_gold()
    if "--keep-gold" in sys.argv and previous and previous.get("gold"):   # the Pages deploy: its warehouse is the small CI fixture, never score against it
        return {**previous["gold"], "pairs": len(rows)}
    try:
        tally, _wrong, stale = gold.evaluate(rows)
        t = tally["all"]
        return {"pairs": len(rows), "wrong_merges": t["fp"], "missed": t["fn"], "stale": len(stale)}
    except Exception as e:  # no database in this checkout, or the DuckDB UI holds it open
        if previous and previous.get("gold"):
            print(f"gold set not re-scored ({type(e).__name__}); keeping the previous values", file=sys.stderr)
            return {**previous["gold"], "pairs": len(rows)}
        sys.exit(f"gold set cannot be scored and there are no previous values: {e}")


def overture_numbers() -> dict:
    b = json.loads(BENCH.read_text(encoding="utf-8"))
    fetched = sum(b["themes"][t]["extract_step"]["bytes"] for t in ("places", "addresses"))
    size = sum(b["themes"][t]["release_bytes"] for t in ("places", "addresses"))
    return {"release": b["release"], "run_on": b["run_on"], "fetched_mb": round(fetched / 1e6), "themes_gb": round(size / 1e9, 1)}


def load_numbers() -> dict:
    """What a phone downloads before the map shows pins (data/map.json, ingestion/split_app_data.py) vs the whole export, gzipped as
    GitHub Pages serves it, and the time saved at Lighthouse's mobile test speed (1.6 Mbps). An estimate, not a field measurement."""
    import gzip
    from split_app_data import j, split

    full = VENUES.read_bytes()
    core, det = split(json.loads(full))
    gz = lambda b: len(gzip.compress(b, 6))
    whole, first = gz(full), gz(j(core).encode("utf-8"))
    return {"export_gz_kb": round(whole / 1000), "first_gz_kb": round(first / 1000), "details_gz_kb": round(gz(j(det).encode("utf-8")) / 1000),
            "saved_s_slow4g": round((whole - first) * 8 / 1638400, 1)}


def adrs_superseded() -> int:
    n = 0
    for f in (ROOT / "docs" / "decisions").glob("[0-9][0-9][0-9][0-9]-*.md"):
        if re.search(r"status:?\**:?\s*superseded", f.read_text(encoding="utf-8")[:1500], re.I):
            n += 1
    return n


def build() -> dict:
    t = last_trend_row()
    meta = json.loads(VENUES.read_text(encoding="utf-8"))["meta"]
    previous = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else None
    return {
        "as_of": meta["generated"],
        "scorecard_as_of": t["date"],
        "venues": int(meta["venues"]),
        "sports_with_venues": int(meta["sports_with_venues"]),
        "sports_total": int(meta["sports_total"]),
        "export_mb": round(VENUES.stat().st_size / 1e6, 1),
        "adrs_superseded": adrs_superseded(),
        "named_pct": float(t["named_pct"]),
        "sla_met": int(t["sla_met"]),
        "sla_total": int(t["sla_total"]),
        "tests_pass": int(t["tests_pass"]),
        "tests_fail": int(t["tests_fail"]),
        "models": len(list((ROOT / "transform" / "models").rglob("*.sql"))),
        "seeds": len(list((ROOT / "transform" / "seeds").glob("*.csv"))),
        "custom_tests": len(list((ROOT / "transform" / "tests").glob("*.sql"))),
        "adrs": len(list((ROOT / "docs" / "decisions").glob("[0-9][0-9][0-9][0-9]-*.md"))),
        "ci_checks": len(list((ROOT / "ci").glob("check_*.py"))),
        "gold": gold_numbers(previous),
        "overture": overture_numbers(),
        "history": history_rows(),
        "agent_runs": agent_run_rows(),
        "ask": ask_numbers(previous, meta["generated"]),
        "load": load_numbers(),
    }


def ask_numbers(previous: dict | None, today: str) -> dict:
    """Ask box quality: the test set's pass count and the last 7 days of questions (ending today) and misses."""
    import datetime
    import subprocess
    tests = (previous or {}).get("ask", {}).get("tests") or {"passed": None, "total": None}
    try:
        out = subprocess.run(["node", str(ROOT / "chatbot" / "test_ask.js")], capture_output=True, text=True, timeout=300, cwd=ROOT).stdout
        m = re.search(r"^(\d+)/(\d+) passed$", out, re.M)
        if m:
            tests = {"passed": int(m.group(1)), "total": int(m.group(2))}
    except (OSError, subprocess.SubprocessError) as e:
        print(f"Ask box tests not run ({type(e).__name__}); keeping the previous values", file=sys.stderr)
    end = datetime.date.fromisoformat(today)
    start = (end - datetime.timedelta(days=6)).isoformat()
    asked = missed = 0
    if USAGE_EVENTS.exists():
        with USAGE_EVENTS.open(encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if not (start <= r["day"] <= today):
                    continue
                if r["event"] == "ask-kind":
                    asked += int(r["count"])
                    missed += int(r["count"]) if r["detail"].lower() in ASK_MISS_KINDS else 0
                elif r["event"] == "ask-empty":
                    missed += int(r["count"])
    return {"tests": tests, "week_from": start, "week_to": today, "asked": asked, "missed": missed}


# The "at a glance" numbers in the story docs, filled from this file so they never trail the map. Only `--docs` (make stats) writes them:
# the refresh agent runs plain build_stats.py, so its PRs stay inside the R0 allowlist (ci/check_refresh_diff.py). --check warns when they trail.
STORY = {
    "docs/case_study.md": lambda d: [
        f"- **{d['venues']:,} venues** from three source families, {d['sports_with_venues']} of {d['sports_total']} sports with at least one venue, {d['sla_met']} of {d['sla_total']} service levels met (scorecard `make quality`, {d['scorecard_as_of']}).",
        f"- **{d['models']} dbt models, {d['seeds']} seeds, {d['custom_tests']} custom SQL tests**, plus column tests ({d['tests_pass']} dbt tests passing); **{d['adrs']} decision records**; {d['ci_checks']} CI gate scripts.",
        f"- **Entity resolution measured on a gold set:** {d['gold']['pairs']} labelled pairs, {d['gold']['wrong_merges']} wrong merges, {d['gold']['missed']} missed.",
        f"- **Reads about {round(100 * d['overture']['fetched_mb'] / (d['overture']['themes_gb'] * 1000))}% of a {d['overture']['themes_gb']:.0f} GB columnar source** ({d['overture']['fetched_mb']:,} MB fetched of {d['overture']['themes_gb']} GB, places and addresses themes).",
        f"- **No server, no database service, $0 hosting:** one {d['export_mb']} MB JSON export on GitHub Pages.",
        *([f"- **Fast on phones:** the map first downloads only what draws the pins, {d['load']['first_gz_kb']:,} KB instead of {d['load']['export_gz_kb']:,} KB (gzip), so it opens about {d['load']['saved_s_slow4g']} s sooner on a slow phone connection (estimate at 1.6 Mbps); addresses and links follow."] if d.get("load") else []),
        *([f"- **Ask box:** {d['ask']['tests']['passed']} of {d['ask']['tests']['total']} test questions answered right, rule-based with no AI model; CI runs the set on every change."] if d.get("ask", {}).get("tests", {}).get("total") else []),
        f"- *Numbers as of {d['as_of']}, filled in by `make stats`; the live figures are on [How it's built](https://abov.github.io/courtconnect-ca/how-its-built.html).*",
    ],
    "docs/talk_outline.md": lambda d: [
        f"1. **What:** a free map of racket-sport venues in California, Nevada, Oregon, Washington, Arizona, New Mexico, Texas and Hawaii (plus a Mexico pilot), for sports where a tennis court and a padel court are not the same pin. {d['venues']:,} venues; {d['sports_with_venues']} of {d['sports_total']} sports have at least one ([scorecard](data_quality_trend.csv), {d['scorecard_as_of']}).",
        f"2. **How:** Python ingestion, dbt on DuckDB, one {d['export_mb']} MB JSON file on GitHub Pages. No server, no accounts, $0 hosting ([running costs](running_costs.md)).",
        f"3. **The interesting part:** I measure it. A labelled test set scores the place matcher ({d['gold']['pairs']} pairs, {d['gold']['wrong_merges']} wrong merges, {d['gold']['missed']} missed). A scorecard has stated service levels, published even when they miss: {d['sla_met']} of {d['sla_total']} met, and {d['named_pct']}% of venues have a real name.",
    ],
}
BEGIN, END = "<!-- numbers: filled in by make stats (ingestion/build_stats.py, STORY); edit the template there -->", "<!-- /numbers -->"


def story_docs(d: dict) -> dict[str, tuple[str, str]]:
    """{path: (current text, text with the numbers block refreshed)}"""
    out = {}
    for rel, lines in STORY.items():
        p = ROOT / rel
        text = p.read_text(encoding="utf-8")
        m = re.search(re.escape(BEGIN) + r"\n.*?" + re.escape(END), text, re.S)
        if not m:
            sys.exit(f"{rel} has no numbers block ({BEGIN} ... {END})")
        out[rel] = (text, text[:m.start()] + BEGIN + "\n" + "\n".join(lines(d)) + "\n" + END + text[m.end():])
    return out


def check() -> None:
    problems = []
    if not OUT.exists():
        sys.exit(f"{OUT.relative_to(ROOT)} is missing: run `make stats` and commit it")
    d = json.loads(OUT.read_text(encoding="utf-8"))
    for k in KEYS:
        if k not in d:
            problems.append(f"missing key: {k}")
    if not problems:
        if d["scorecard_as_of"] != last_trend_row()["date"]:
            problems.append(f"scorecard_as_of {d['scorecard_as_of']} is not the newest scorecard row {last_trend_row()['date']}: run `make stats` after `make quality`")
        for k in ("venues", "sports_total", "models", "seeds", "adrs"):
            if not isinstance(d[k], int) or d[k] <= 0:
                problems.append(f"{k} must be a positive integer")
        if d["history"] != history_rows():
            problems.append("history differs from docs/data_quality_trend.csv: run `make stats`")
        if d["agent_runs"] != agent_run_rows():
            problems.append("agent_runs differs from docs/agent_log.csv: run `make stats` after the agent appends its log row")
        if not isinstance(d["ask"].get("asked"), int) or not isinstance(d["ask"].get("missed"), int):
            problems.append("ask needs asked and missed counts: run `make stats`")
        if d["gold"].get("wrong_merges") is None or d["gold"].get("missed") is None:
            problems.append("gold needs wrong_merges and missed")
    if problems:
        sys.exit("build_stats.json check failed:\n  " + "\n  ".join(problems))
    trailing = [rel for rel, (cur, new) in story_docs(d).items() if cur != new]
    if trailing:   # a warning, not a failure: refresh PRs update the json but not the docs
        print(f"::warning::numbers in {', '.join(trailing)} trail app/data/build_stats.json: run `make stats` (it passes --docs) and commit")
    print(f"build_stats.json ok: as of {d['as_of']} (scorecard {d['scorecard_as_of']}), {d['venues']} venues, gold set {d['gold']['pairs']} pairs")


def main() -> None:
    if "--check" in sys.argv:
        return check()
    d = build()
    OUT.write_text(json.dumps(d, indent=1) + "\n", encoding="utf-8")
    if "--docs" in sys.argv:
        for rel, (cur, new) in story_docs(d).items():
            if cur != new:
                (ROOT / rel).write_text(new, encoding="utf-8")
                print(f"Updated the numbers in {rel}")
    print(f"Wrote {OUT.relative_to(ROOT)}: as of {d['as_of']}, {d['venues']} venues, {d['models']} models, {d['tests_pass']} dbt tests passing, "
          f"gold set {d['gold']['pairs']} pairs ({d['gold']['wrong_merges']} wrong, {d['gold']['missed']} missed)")


if __name__ == "__main__":
    main()
