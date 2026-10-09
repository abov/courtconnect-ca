"""Load the extracted CSVs into the RAW layer of DuckDB (default) or Snowflake.

    python ingestion/load_raw.py                      # DuckDB (local)
    python ingestion/load_raw.py --target snowflake   # Snowflake (needs .env)

Each load is a full refresh of its landing table, so re-running is safe (idempotent).
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

# landing table -> source csv name, and the numeric columns to cast
TABLES = {
    "osm_courts": ("osm_courts.csv", ["osm_id", "lat", "lon"]),
    "osm_parents": ("osm_parents.csv", ["osm_id", "minlat", "minlon", "maxlat", "maxlon"]),
    "overture_places": ("overture_places.csv", ["lat", "lon", "confidence"]),
    "google_place_ids": ("google_place_ids.csv", []),
}

# Tables that may legitimately have no file yet (the Google lookup is opt-in). They load as empty tables with
# these columns, so dbt models that read them still build.
OPTIONAL = {"google_place_ids": ["venue_id", "google_place_id", "resolved_at"]}


def load_duckdb(table: str, df: pd.DataFrame, db_path: str) -> None:
    import duckdb

    con = duckdb.connect(db_path)
    con.execute("create schema if not exists raw")
    con.register("df", df)
    con.execute(f"create or replace table raw.{table} as select * from df")
    n = con.execute(f"select count(*) from raw.{table}").fetchone()[0]
    print(f"DuckDB: raw.{table} now has {n:,} rows")
    con.close()


def snowflake_connection():
    import snowflake.connector

    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.environ.get("SNOWFLAKE_ROLE", "COURTCONNECT_DEV"),
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "COURTCONNECT_WH"),
        database=os.environ.get("SNOWFLAKE_DATABASE", "COURTCONNECT"),
    )


def load_snowflake(conn, table: str, df: pd.DataFrame) -> None:
    from snowflake.connector.pandas_tools import write_pandas

    df = df.copy()
    df.columns = [c.upper() for c in df.columns]
    ok, _, nrows, _ = write_pandas(
        conn, df, table.upper(), schema="RAW",
        auto_create_table=True, overwrite=True, quote_identifiers=False,
    )
    print(f"Snowflake: RAW.{table.upper()} loaded ({nrows:,} rows, ok={ok})")


def main() -> None:
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=["duckdb", "snowflake"], default="duckdb")
    ap.add_argument("--duckdb-path", default="courtconnect.duckdb")
    ap.add_argument("--data-dir", default="data/raw", help="folder holding the extracted CSVs (CI uses ci/fixtures)")
    args = ap.parse_args()

    conn = None
    if args.target == "snowflake":
        conn = snowflake_connection()
        conn.cursor().execute("create schema if not exists RAW")
    try:
        for table, (csv_name, numeric) in TABLES.items():
            csv_path = str(Path(args.data_dir) / csv_name)
            if Path(csv_path).exists():
                df = pd.read_csv(csv_path, dtype=str)
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
            if conn is None:
                load_duckdb(table, df, args.duckdb_path)
            else:
                load_snowflake(conn, table, df)
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    main()
