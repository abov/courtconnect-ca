"""Append today's venue counts (city x sport) to docs/market_snapshots.csv, so openings and closures show up as a trend.

    python ingestion/snapshot_market.py            (or: make market-snapshot)

Run it once per refresh, after `dbt build`. Reads marts.mart_market_gaps from the DuckDB build (known venues only, directly listed sports,
INFERRED like the mart itself). Rows with zero venues are skipped. Re-running on the same day replaces that day's rows.
The warehouse is rebuilt from scratch each time, so this committed CSV is the only history there is.
"""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import duckdb

OUT = Path("docs/market_snapshots.csv")
FIELDS = ["date", "region", "city", "sport_name", "venues", "courts", "public_venues", "members_only_venues"]


def main() -> None:
    today = date.today().isoformat()
    con = duckdb.connect("courtconnect.duckdb", read_only=True)
    rows = con.execute(
        """
        select region, city, sport_name, venues_in_city, courts_in_city, public_venues_in_city, members_only_venues_in_city
        from marts.mart_market_gaps
        where venues_in_city > 0
        order by region, city, sport_name
        """
    ).fetchall()
    new = [dict(zip(FIELDS, (today, *r))) for r in rows]
    old = [r for r in csv.DictReader(OUT.open(encoding="utf-8")) if r["date"] != today] if OUT.exists() else []
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(old + new)
    print(f"Wrote {len(new)} rows for {today} to {OUT} ({len(old)} older rows kept)")


if __name__ == "__main__":
    main()
