"""Roll the GoatCounter export up for the dashboard: docs/usage_daily.csv (page views and events per day) and
docs/usage_events.csv (events per day, event name and detail).

    python ingestion/extract_goatcounter.py --days 60     # needs GOATCOUNTER_API_TOKEN; 90 days errors on this young site
    python ingestion/usage_daily.py                       # merges into docs/usage_daily.csv (new days replace old ones, older days stay)

Counts and dates only. usage_events.csv carries the event vocabulary from docs/goat_analysis.md (event name, plus its sport, city,
domain or reply kind); never typed text, venue names or visitors. The Pages build has no token, so the dashboard reads these
committed files (dashboard/README.md). Commit them after each run.
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
EVENTS_OUT = Path(__file__).resolve().parents[1] / "docs" / "usage_events.csv"


def split_event(path: str, title: str) -> tuple[str, str]:
    """event/sport-pick/pop-tennis (title "Pop Tennis") -> ("sport-pick", "Pop Tennis"); event/venue-open -> ("venue-open", "")."""
    parts = path.lstrip("/").split("/", 2)[1:]
    if not parts or not parts[0]:
        return "", ""
    return parts[0], (title or parts[1]) if len(parts) > 1 else ""


def main() -> None:
    src = Path(raw_path("goatcounter_daily.csv"))
    if not src.exists():
        sys.exit(f"{src} not found: run ingestion/extract_goatcounter.py first.")
    fresh: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    ev: dict[tuple[str, str, str], int] = defaultdict(int)
    with src.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            is_event = r["is_event"].lower() == "true"
            fresh[r["day"]][1 if is_event else 0] += int(r["count"])
            if is_event:
                name, detail = split_event(r["path"], r["title"])
                if name == "ask-feedback":   # typed text a visitor chose to send: counted, but the text stays out of the committed file (extract_ask_feedback.py)
                    detail = ""
                if name:
                    ev[(r["day"], name, detail)] += int(r["count"])
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

    # same merge for the event rows: a refreshed day replaces its old rows, older days stay
    old: list[list[str]] = []
    if EVENTS_OUT.exists():
        with EVENTS_OUT.open(encoding="utf-8") as f:
            old = [[r["day"], r["event"], r["detail"], r["count"]] for r in csv.DictReader(f) if r["day"] not in fresh]
    rows = old + [[d, n, x, str(c)] for (d, n, x), c in ev.items()]
    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    with EVENTS_OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["day", "event", "detail", "count"])
        w.writerows(rows)
    print(f"{len(rows)} event rows -> {EVENTS_OUT}")


if __name__ == "__main__":
    main()
