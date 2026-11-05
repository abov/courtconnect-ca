"""Write the aggregate CSVs the Evidence.dev dashboard reads (dashboard/sources/courtconnect/*.csv).

    python ingestion/export_dashboard_data.py        (or: make dashboard-data)

Only counts and dates that are already public leave the warehouse: the scorecard history, the numbers on the How it's built page
(app/data/build_stats.json), the feedback issue counts (docs/feedback_log.csv), daily site views (docs/usage_daily.csv) and the per-sport venue counts from the map export. No venue rows, addresses or contacts. The CSVs are
generated and git-ignored; run `make quality`, `make stats` and `make app-data` first so they are current.
"""
from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dashboard" / "sources" / "courtconnect"


def write(name: str, header: list[str], rows: list[list]) -> None:
    with (OUT / name).open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote dashboard/sources/courtconnect/{name}: {len(rows)} rows")


def live_issues() -> list[tuple[str, str]] | None:
    """(opened, closed) dates for every GitHub issue, straight from GitHub, so the scheduled Pages build is current.
    Only runs in CI (GITHUB_ACTIONS); locally, and on any failure, the dashboard falls back to docs/feedback_log.csv."""
    if not os.environ.get("GITHUB_ACTIONS"):
        return None
    try:
        out = subprocess.run(["gh", "issue", "list", "--state", "all", "--limit", "2000", "--json", "createdAt,closedAt"],
                             capture_output=True, text=True, check=True, timeout=60).stdout
        return [(i["createdAt"][:10], (i["closedAt"] or "")[:10]) for i in json.loads(out)]
    except (subprocess.SubprocessError, OSError, ValueError, KeyError):
        print("live issue fetch failed; using docs/feedback_log.csv")
        return None


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "docs" / "data_quality_trend.csv", OUT / "trend.csv")
    print("wrote dashboard/sources/courtconnect/trend.csv: copy of docs/data_quality_trend.csv")

    s = json.loads((ROOT / "app" / "data" / "build_stats.json").read_text(encoding="utf-8"))
    write("stats.csv",
          ["as_of", "venues", "sports_with_venues", "sports_total", "named_pct", "sla_met", "sla_total", "tests_pass", "models", "seeds", "adrs",
           "gold_pairs", "gold_wrong_merges", "gold_missed"],
          [[s["as_of"], s["venues"], s["sports_with_venues"], s["sports_total"], s["named_pct"], s["sla_met"], s["sla_total"], s["tests_pass"],
            s["models"], s["seeds"], s["adrs"], s["gold"]["pairs"], s["gold"]["wrong_merges"], s["gold"]["missed"]]])

    # Feedback issues: one row per day from the first report to today, so the chart shows open vs handled over time.
    log = live_issues()
    if log is None:
        with (ROOT / "docs" / "feedback_log.csv").open(encoding="utf-8") as f:
            log = [(r["received_on"], r["resolved_on"]) for r in csv.DictReader(f) if r["channel"] == "github-issue"]
    if log:
        opened, closed = Counter(o for o, _ in log), Counter(c for _, c in log if c)
        day, end, rows, n_open = date.fromisoformat(min(opened)), date.today(), [], 0
        while day <= end:
            k = day.isoformat()
            n_open += opened[k] - closed[k]
            rows.append([k, opened[k], closed[k], n_open])
            day += timedelta(days=1)
        write("issues.csv", ["date", "opened", "closed", "open_now"], rows)

    shutil.copyfile(ROOT / "docs" / "usage_daily.csv", OUT / "views.csv")
    print("wrote dashboard/sources/courtconnect/views.csv: copy of docs/usage_daily.csv")

    venues = json.loads((ROOT / "app" / "data" / "venues.json").read_text(encoding="utf-8"))
    write("sport_coverage.csv", ["sport", "venues", "status"], [[x["n"], x["v"], x["s"]] for x in venues["sports"]])


if __name__ == "__main__":
    main()
