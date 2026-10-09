"""Load data/raw/osm_courts.csv into the RAW layer of DuckDB (default) or Snowflake.

    python ingestion/load_raw.py                      # DuckDB (local)
    python ingestion/load_raw.py --target snowflake   # Snowflake (needs .env)

The load is a full refresh of one landing table, so re-running is safe (idempotent).
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

TABLE = "osm_courts"


def load_duckdb(df: pd.DataFrame, db_path: str) -> None:
    import duckdb

    con = duckdb.connect(db_path)
    con.execute("create schema if not exists raw")
    con.register("df", df)
    con.execute(f"create or replace table raw.{TABLE} as select * from df")
    n = con.execute(f"select count(*) from raw.{TABLE}").fetchone()[0]
    print(f"DuckDB: raw.{TABLE} now has {n:,} rows")


def load_snowflake(df: pd.DataFrame) -> None:
    import snowflake.connector
    from snowflake.connector.pandas_tools import write_pandas

    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.environ.get("SNOWFLAKE_ROLE", "COURTCONNECT_DEV"),
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "COURTCONNECT_WH"),
        database=os.environ.get("SNOWFLAKE_DATABASE", "COURTCONNECT"),
    )
    try:
        conn.cursor().execute("create schema if not exists RAW")
        df.columns = [c.upper() for c in df.columns]
        ok, _, nrows, _ = write_pandas(
            conn, df, TABLE.upper(), schema="RAW",
            auto_create_table=True, overwrite=True, quote_identifiers=False,
        )
        print(f"Snowflake: RAW.{TABLE.upper()} loaded ({nrows:,} rows, ok={ok})")
    finally:
        conn.close()


def main() -> None:
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=["duckdb", "snowflake"], default="duckdb")
    ap.add_argument("--csv", default="data/raw/osm_courts.csv")
    ap.add_argument("--duckdb-path", default="courtconnect.duckdb")
    args = ap.parse_args()

    if not Path(args.csv).exists():
        raise SystemExit(f"{args.csv} not found - run extract_osm_courts.py first")
    df = pd.read_csv(args.csv, dtype=str)
    df["lat"] = pd.to_numeric(df["lat"])
    df["lon"] = pd.to_numeric(df["lon"])
    df["osm_id"] = pd.to_numeric(df["osm_id"])

    load_duckdb(df, args.duckdb_path) if args.target == "duckdb" else load_snowflake(df)


if __name__ == "__main__":
    main()
