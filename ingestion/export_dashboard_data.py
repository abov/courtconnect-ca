"""Write the aggregate CSVs the Evidence.dev dashboard reads (dashboard/sources/courtconnect/*.csv).

    python ingestion/export_dashboard_data.py        (or: make dashboard-data)

Only counts and dates that are already public leave the warehouse: the scorecard history, the numbers on the How it's built page
(app/data/build_stats.json) and the per-sport venue counts from the map export. No venue rows, addresses or contacts. The CSVs are
generated and git-ignored; run `make quality`, `make stats` and `make app-data` first so they are current.
"""
from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dashboard" / "sources" / "courtconnect"


def write(name: str, header: list[str], rows: list[list]) -> None:
    with (OUT / name).open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote dashboard/sources/courtconnect/{name}: {len(rows)} rows")


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

    venues = json.loads((ROOT / "app" / "data" / "venues.json").read_text(encoding="utf-8"))
    write("sport_coverage.csv", ["sport", "venues", "status"], [[x["n"], x["v"], x["s"]] for x in venues["sports"]])


if __name__ == "__main__":
    main()
