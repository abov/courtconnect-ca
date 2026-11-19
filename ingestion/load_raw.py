"""Load the extracted CSVs into the RAW layer of DuckDB (the only warehouse, ADR 0018).

    python ingestion/load_raw.py

Each load is a full refresh of its landing table, so re-running is safe (idempotent).
"""
from __future__ import annotations

import argparse
from pathlib import Path

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
    "ask_feedback": ("ask_feedback.csv", []),   # questions visitors sent from the ask box (extract_ask_feedback.py); local warehouse only
}

# Tables that may legitimately have no file yet (the Google lookup is opt-in). They load as empty tables with
# these columns, so dbt models that read them still build.
OPTIONAL = {"overture_addresses": ["address_id", "house_number", "street", "unit", "postcode", "city", "state", "lat", "lon", "release"],
            "osm_walls": ["osm_type", "osm_id", "lat", "lon", "name", "sport", "surface", "lit", "access", "fee", "operator", "leisure",
                         "tennis", "addr_city", "extracted_at", "region"],
            "google_place_ids": ["venue_id", "google_place_id", "resolved_at"],
            "website_checks": ["domain", "status", "resolved_host", "checked_at"],
            "census_boundaries": ["kind", "state_fips", "geoid", "name", "wkt", "source", "extracted_at"],
            "ask_feedback": ["day", "question", "count"]}


# The strings pandas read as missing, so the load matches the old pandas one ("N/A" street suffixes, "#NA" units were NULL).
NULLS = ("['', '#N/A', '#N/A N/A', '#NA', '-1.#IND', '-1.#QNAN', '-NaN', '-nan', '1.#IND', '1.#QNAN', '<NA>', 'N/A', 'NA', "
         "'NULL', 'NaN', 'None', 'n/a', 'nan', 'null']")


def _sql_list(paths) -> str:
    return "[" + ", ".join("'" + str(p).replace("\\", "/").replace("'", "''") + "'" for p in paths) + "]"


def load_duckdb(con, table: str, files: list[Path], numeric: list[str], force: bool = False) -> None:
    """Full refresh of raw.<table> from CSV files, read by DuckDB itself (no pandas: 10M address rows took ~2 min that way).

    Every column lands as text except `numeric` ones (osm_id is BIGINT, the rest DOUBLE); a column that is empty in this batch
    must not be guessed as INTEGER by the warehouse and break lower().
    """
    if files:
        cols = [r[0] for r in con.execute(f"select column_name from (describe select * from read_csv({_sql_list(files)}, "
                                          f"all_varchar=true, union_by_name=true, nullstr={NULLS}))").fetchall()]
        casts = ", ".join(f'cast("{c}" as {"BIGINT" if c == "osm_id" else "DOUBLE"}) as "{c}"' for c in cols if c in numeric)
        sel = f"select * replace ({casts})" if casts else "select *"
        con.execute(f"create or replace temp table _load as {sel} from read_csv({_sql_list(files)}, all_varchar=true, union_by_name=true, nullstr={NULLS})")
    else:
        cols = OPTIONAL[table]
        defs = ", ".join(f'"{c}" {"DOUBLE" if c in numeric else "VARCHAR"}' for c in cols)
        con.execute(f"create or replace temp table _load ({defs})")
    new = con.execute("select count(*) from _load").fetchall()[0][0]
    # Guard against loading a stale CSV over newer data (an old copy once cut raw.osm_walls from 888 to 263 rows).
    exists = con.execute("select count(*) from information_schema.tables where table_schema = 'raw' and table_name = ?",
                         [table]).fetchall()[0][0]
    old = con.execute(f"select count(*) from raw.{table}").fetchall()[0][0] if exists else 0
    if old >= 50 and new < 0.9 * old and not force:
        raise SystemExit(f"raw.{table} would shrink from {old:,} to {new:,} rows: the CSV in the data folder looks "
                         f"older than the database. Refresh the CSV, or pass --force if the drop is intended.")
    con.execute(f"create or replace table raw.{table} as select * from _load")
    con.execute("drop table _load")
    print(f"DuckDB: raw.{table} now has {new:,} rows")


def main() -> None:
    import duckdb

    ap = argparse.ArgumentParser()
    ap.add_argument("--duckdb-path", default="courtconnect.duckdb")
    ap.add_argument("--data-dir", default=raw_path(""), help="folder holding the extracted CSVs (CI uses ci/fixtures)")
    ap.add_argument("--force", action="store_true", help="load even if a table would shrink by more than 10%")
    args = ap.parse_args()

    con = duckdb.connect(args.duckdb_path)
    con.execute("create schema if not exists raw")
    for table, (csv_name, numeric) in TABLES.items():
        csv_path = Path(args.data_dir) / csv_name
        files: list[Path] = []
        if csv_path.exists():
            files = [csv_path]
            # Per-region extras (e.g. osm_courts_nv.csv from `--area nevada`, any two-letter state code) are appended (ADR 0014, 0028).
            files += sorted(Path(args.data_dir).glob(Path(csv_name).stem + "_??.csv"))
        elif table not in OPTIONAL:
            raise SystemExit(f"{csv_path} not found - run the matching extract_*.py first")
        load_duckdb(con, table, files, numeric, args.force)
    con.close()


if __name__ == "__main__":
    main()
