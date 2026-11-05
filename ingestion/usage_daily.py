"""Roll the GoatCounter export up to one row per day (page views, events) in docs/usage_daily.csv for the dashboard.

    python ingestion/extract_goatcounter.py --days 60     # needs GOATCOUNTER_API_TOKEN; 90 days errors on this young site
    python ingestion/usage_daily.py                       # merges into docs/usage_daily.csv (new days replace old ones, older days stay)

Counts and dates only: no paths, titles or visitors leave the raw export. The Pages build has no token, so the dashboard reads this
committed file (dashboard/README.md). Commit it after each run.
"""
from __future__ import annotations

import csv
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from rawdir import raw_path  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "docs" / "usage_daily.csv"


def main() -> None:
    src = Path(raw_path("goatcounter_daily.csv"))
    if not src.exists():
        sys.exit(f"{src} not found: run ingestion/extract_goatcounter.py first.")
    fresh: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    with src.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            fresh[r["day"]][1 if r["is_event"].lower() == "true" else 0] += int(r["count"])
    merged: dict[str, list[int]] = {}
    if OUT.exists():
        with OUT.open(encoding="utf-8") as f:
            merged = {r["day"]: [int(r["page_views"]), int(r["events"])] for r in csv.DictReader(f)}
    merged.update(fresh)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["day", "page_views", "events"])
        w.writerows([d, *merged[d]] for d in sorted(merged))
    print(f"{len(merged)} days ({len(fresh)} refreshed) -> {OUT}")


if __name__ == "__main__":
    main()
