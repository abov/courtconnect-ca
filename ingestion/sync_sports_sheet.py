"""Sync the racket-sports master list from the Google Sheet into the dbt seed `all_racquet`.

The sheet (tab "All Raquet") is the source of truth for which sports the platform supports.
It must be shared as "Anyone with the link can view" for the export URL to work.

    python ingestion/sync_sports_sheet.py

Writes transform/seeds/all_racquet.csv (headers snake_cased, fully blank rows dropped, values otherwise
untouched, apart from the https/blurb-length checks on the info-card columns - cleaning happens in dbt so it is tested and visible in lineage).
"""
from __future__ import annotations

import csv
import io
import sys
from pathlib import Path

import os

import requests
from dotenv import load_dotenv
from useragent import HEADERS

# The sheet's location lives in .env (gitignored), not in the repo:
#   SPORTS_SHEET_ID=<the long id in the sheet's URL>     SPORTS_SHEET_GID=0   (the tab; 0 = "All Raquet")
load_dotenv()
SHEET_ID = os.environ.get("SPORTS_SHEET_ID", "").strip()
SHEET_GID = os.environ.get("SPORTS_SHEET_GID", "0").strip() or "0"
EXPORT_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"
EXPECTED_SPORTS = 82  # keep in sync with var `expected_racket_sports` in transform/dbt_project.yml

COLUMNS = {
    "Type": "sport_type", "Sport": "sport", "Players": "players", "Class": "popularity_class",
    "Org": "org", "Yr Origin": "year_origin", "Active Loc": "active_loc", "Court Dim": "court_dim",
    "Court Surface": "court_surface", "Base Gear": "base_gear", "Net Type": "net_type",
    "Net Ht": "net_ht", "Gear Avail (AO)": "gear_avail_ao", "Competing": "competing", "url": "url",
}
# Added 2026-10-18 (sport info card, docs/sport_discovery_plan.md Part 2). Optional so a sheet without them still syncs; the seed
# always gets the columns (blank until the sheet has them). Links must be https; the blurb is shown as plain text.
DETAIL_COLUMNS = {"Blurb": "blurb", "Learn URL": "learn_url", "Rules URL": "rules_url", "Court URL": "court_url", "Gear URL": "gear_url"}
MAX_BLURB = 200
OUT = Path("transform/seeds/all_racquet.csv")


def main() -> None:
    if not SHEET_ID:
        sys.exit("SPORTS_SHEET_ID is not set. Add it to .env (see .env.example). It is the long id in the sheet's URL.")
    r = requests.get(EXPORT_URL, timeout=60, headers=HEADERS)
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
        out.update({v: (row.get(k) or "").strip() for k, v in DETAIL_COLUMNS.items()})
        if out["sport"]:  # the sheet has ~20 formatted-but-empty rows below the data
            rows.append(out)

    for r in rows:
        for c in ("learn_url", "rules_url", "court_url", "gear_url"):
            if r[c] and not r[c].startswith("https://"):
                sys.exit(f"{r['sport']}: {c} must start with https:// (got {r[c]!r}). Fix it in the sheet.")
        if len(r["blurb"]) > MAX_BLURB:
            sys.exit(f"{r['sport']}: blurb is {len(r['blurb'])} characters (max {MAX_BLURB}). Shorten it in the sheet.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(COLUMNS.values()) + list(DETAIL_COLUMNS.values()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(rows)} sports to {OUT}  (source: your Google Sheet, id kept in .env)")
    if len(rows) != EXPECTED_SPORTS:
        print(f"WARNING: expected {EXPECTED_SPORTS} sports, found {len(rows)}. "
              f"Add the missing sport(s) to the sheet or update EXPECTED_SPORTS.", file=sys.stderr)


if __name__ == "__main__":
    main()
