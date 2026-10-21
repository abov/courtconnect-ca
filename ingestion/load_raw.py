"""Load the extracted CSVs into the RAW layer of DuckDB (the only warehouse, ADR 0018).

    python ingestion/load_raw.py

Each load is a full refresh of its landing table, so re-running is safe (idempotent).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from rawdir import raw_path

# landing table -> source csv name, and the numeric columns to cast
TABLES = {
    "osm_courts": ("osm_courts.csv", ["osm_id", "lat", "lon"]),
    "osm_walls": ("osm_walls.csv", ["osm_id", "lat", "lon"]),
    "osm_parents": ("osm_parents.csv", ["osm_id", "minlat", "minlon", "maxlat", "maxlon"]),
    "overture_places": ("overture_places.csv", ["lat", "lon", "confidence"]),
    "overture_addresses": ("overture_addresses.csv", ["lat", "lon"]),
    "google_place_ids": ("google_place_ids.csv", []),
    "website_checks": ("website_checks.csv", []),
    "census_boundaries": ("census_boundaries.csv", []),   # reference polygons (extract_census_boundaries.py); read by place_from_boundaries.py
}

# Tables that may legitimately have no file yet (the Google lookup is opt-in). They load as empty tables with
# these columns, so dbt models that read them still build.
OPTIONAL = {"overture_addresses": ["address_id", "house_number", "street", "unit", "postcode", "city", "state", "lat", "lon", "release"],
            "osm_walls": ["osm_type", "osm_id", "lat", "lon", "name", "sport", "surface", "lit", "access", "fee", "operator", "leisure",
                         "tennis", "addr_city", "extracted_at", "region"],
            "google_place_ids": ["venue_id", "google_place_id", "resolved_at"],
            "website_checks": ["domain", "status", "resolved_host", "checked_at"],
            "census_boundaries": ["kind", "state_fips", "geoid", "name", "wkt", "source", "extracted_at"]}


def load_duckdb(table: str, df: pd.DataFrame, db_path: str, force: bool = False) -> None:
    import duckdb

    con = duckdb.connect(db_path)
    con.execute("create schema if not exists raw")
    # Guard against loading a stale CSV over newer data (an old copy once cut raw.osm_walls from 888 to 263 rows).
    exists = con.execute("select count(*) from information_schema.tables where table_schema = 'raw' and table_name = ?",
                         [table]).fetchall()[0][0]
    old = con.execute(f"select count(*) from raw.{table}").fetchall()[0][0] if exists else 0
    if old >= 50 and len(df) < 0.9 * old and not force:
        con.close()
        raise SystemExit(f"raw.{table} would shrink from {old:,} to {len(df):,} rows: the CSV in the data folder looks "
                         f"older than the database. Refresh the CSV, or pass --force if the drop is intended.")
    con.register("df", df)
    con.execute(f"create or replace table raw.{table} as select * from df")
    n = con.execute(f"select count(*) from raw.{table}").fetchall()[0][0]
    print(f"DuckDB: raw.{table} now has {n:,} rows")
    con.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--duckdb-path", default="courtconnect.duckdb")
    ap.add_argument("--data-dir", default=raw_path(""), help="folder holding the extracted CSVs (CI uses ci/fixtures)")
    ap.add_argument("--force", action="store_true", help="load even if a table would shrink by more than 10%")
    args = ap.parse_args()

    for table, (csv_name, numeric) in TABLES.items():
        csv_path = str(Path(args.data_dir) / csv_name)
        if Path(csv_path).exists():
            df = pd.read_csv(csv_path, dtype=str)
            # Per-region extras (e.g. osm_courts_nv.csv from `--area nevada`) are appended (ADR 0014).
            for extra in sorted(Path(args.data_dir).glob(Path(csv_name).stem + "_nv.csv")):
                df = pd.concat([df, pd.read_csv(extra, dtype=str)], ignore_index=True)
        elif table in OPTIONAL:
            df = pd.DataFrame(columns=OPTIONAL[table], dtype=str)
        else:
            raise SystemExit(f"{csv_path} not found - run the matching extract_*.py first")
        for col in df.columns:
            if col in numeric:
                df[col] = pd.to_numeric(df[col])
            else:
                # Pin text columns to a string type: a column that is empty in this batch (say, no court
                # tagged `covered`) must not be guessed as INTEGER by the warehouse and break lower().
                df[col] = df[col].astype("string")
        load_duckdb(table, df, args.duckdb_path, args.force)


if __name__ == "__main__":
    main()
