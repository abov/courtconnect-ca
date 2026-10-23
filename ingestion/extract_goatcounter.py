"""Export daily GoatCounter counts (page views + the named events of ADR 0013) to a raw CSV for analysis.

    python ingestion/extract_goatcounter.py                  # last 90 days -> goatcounter_daily.csv in the shared raw folder
    python ingestion/extract_goatcounter.py --days 30 --out some.csv

Needs GOATCOUNTER_API_TOKEN in .env (GoatCounter -> Settings -> API; permission "Count" is not needed, only
"View statistics"). The token is read from the environment only and never printed. Output columns:
day, path, title, is_event, count. Anonymous aggregate counts only: GoatCounter never gives us a visitor.
Read it with `python ingestion/goat_report.py` (or load it into DuckDB yourself); docs/goat_analysis.md has the metric definitions.
Only the project contact is sent as User-Agent (CLAUDE.md rule).
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from datetime import date, timedelta

import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from rawdir import raw_path  # noqa: E402
from useragent import HEADERS  # noqa: E402

SITE = os.environ.get("GOATCOUNTER_SITE", "courts")   # the part before .goatcounter.com (matches app/index.html)
PAGE = 100


def fetch(token: str, start: date, end: date) -> list[dict]:
    """All paths with a per-day count between start and end (inclusive), following GoatCounter's `more` paging."""
    url = f"https://{SITE}.goatcounter.com/api/v0/stats/hits"
    headers = {**HEADERS, "Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    rows: list[dict] = []
    exclude: list[int] = []
    while True:
        params = {"start": start.isoformat(), "end": end.isoformat(), "limit": PAGE, "daily": "true"}
        if exclude:
            params["exclude_paths"] = ",".join(map(str, exclude))
        r = requests.get(url, headers=headers, params=params, timeout=30)
        if r.status_code == 429:   # rate limited: wait and retry the same page
            time.sleep(float(r.headers.get("X-Rate-Limit-Reset", "5")) + 1)
            continue
        r.raise_for_status()
        body = r.json()
        hits = body.get("hits", [])
        for h in hits:
            for s in h.get("stats", []):
                if s.get("daily"):
                    rows.append({"day": s["day"], "path": h["path"], "title": h.get("title", ""),
                                 "is_event": bool(h.get("event")), "count": s["daily"]})
            exclude.append(h["path_id"])
        if not body.get("more") or not hits:
            return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--days", type=int, default=90, help="how many days back to export (default 90)")
    ap.add_argument("--out", default=raw_path("goatcounter_daily.csv"))
    args = ap.parse_args()
    load_dotenv()
    token = os.environ.get("GOATCOUNTER_API_TOKEN", "")
    if not token:
        sys.exit("GOATCOUNTER_API_TOKEN is not set in .env (see .env.example).")
    end = date.today()
    rows = fetch(token, end - timedelta(days=args.days), end)
    rows.sort(key=lambda x: (x["day"], x["path"]))
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["day", "path", "title", "is_event", "count"])
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} rows ({len({r['path'] for r in rows})} paths) -> {args.out}")


if __name__ == "__main__":
    main()
