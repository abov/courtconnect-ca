"""Sync the racket-sports master list from the Google Sheet into the dbt seed `all_racquet`.

The sheet (tab "All Raquet") is the source of truth for which sports the platform supports.
It must be shared as "Anyone with the link can view" for the export URL to work.

    python ingestion/sync_sports_sheet.py

Writes transform/seeds/all_racquet.csv (headers snake_cased, fully blank rows dropped, values otherwise
untouched - cleaning happens in dbt so it is tested and visible in lineage).
"""
from __future__ import annotations

import csv
import io
import sys
from pathlib import Path

import requests

SHEET_ID = "REDACTED_SHEET_ID"
SHEET_GID = 0  # tab "All Raquet"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit?gid={SHEET_GID}"
EXPORT_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"
EXPECTED_SPORTS = 76  # keep in sync with var `expected_racket_sports` in transform/dbt_project.yml

COLUMNS = {
    "Type": "sport_type", "Sport": "sport", "Players": "players", "Class": "popularity_class",
    "Org": "org", "Yr Origin": "year_origin", "Active Loc": "active_loc", "Court Dim": "court_dim",
    "Court Surface": "court_surface", "Base Gear": "base_gear", "Net Type": "net_type",
    "Net Ht": "net_ht", "Gear Avail (AO)": "gear_avail_ao", "Competing": "competing", "url": "url",
}
OUT = Path("transform/seeds/all_racquet.csv")


def main() -> None:
    r = requests.get(EXPORT_URL, timeout=60, headers={"User-Agent": "courtconnect-ca/0.1"})
    r.raise_for_status()
    if "text/csv" not in r.headers.get("content-type", ""):
        sys.exit("Sheet did not return CSV - is it shared as 'Anyone with the link can view'?")

    reader = csv.DictReader(io.StringIO(r.content.decode("utf-8-sig"), newline=""))
    missing = set(COLUMNS) - set(reader.fieldnames or [])
    if missing:
        sys.exit(f"Sheet is missing expected columns: {sorted(missing)}")

    rows = []
    for row in reader:
        out = {COLUMNS[k]: (row.get(k) or "").strip() for k in COLUMNS}
        if out["sport"]:  # the sheet has ~20 formatted-but-empty rows below the data
            rows.append(out)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(COLUMNS.values()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(rows)} sports to {OUT}  (source: {SHEET_URL})")
    if len(rows) != EXPECTED_SPORTS:
        print(f"WARNING: expected {EXPECTED_SPORTS} sports, found {len(rows)}. "
              f"Add the missing sport(s) to the sheet or update EXPECTED_SPORTS.", file=sys.stderr)


if __name__ == "__main__":
    main()
