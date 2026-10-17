"""Extract Overture address points that sit near a map pin, for the address fill (docs/ml_plan.md, tier 2).

Overture publishes every address point it knows (open data, same release as the places we load). We only need the ones
within ~150 m of a pin, so this reads the pin coordinates from data/raw (OSM courts, Overture places) and
seeds/manual_venues.csv, and keeps address points in the 1-cell neighbourhood (0.004 deg, ~440 m) of any pin. dbt picks the
nearest one within 150 m (int_venue_address). No API calls: DuckDB range requests against the public S3 bucket.

    python ingestion/extract_overture_addresses.py                    # newest release
    python ingestion/extract_overture_addresses.py --release 2026-09-23.1

Output: data/raw/overture_addresses.csv (load_raw.py loads it into raw.overture_addresses; CI uses a fixture).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb

from extract_overture_places import BUCKET, latest_release

CELLS_PER_DEGREE = 250   # 0.004 deg cells


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--release", default=None)
    ap.add_argument("--out", default="data/raw/overture_addresses.csv")
    args = ap.parse_args()
    release = args.release or latest_release()
    print(f"Overture release {release}")

    con = duckdb.connect()
    con.execute("install httpfs; load httpfs; set s3_region='us-west-2';")
    con.execute("""create table pins as
        select lat, lon from read_csv_auto('data/raw/osm_courts.csv') where lat is not null and lon is not null
        union all select lat, lon from read_csv_auto('data/raw/overture_places.csv') where lat is not null and lon is not null
        union all select lat, lon from read_csv_auto('transform/seeds/manual_venues.csv') where lat is not null and lon is not null""")
    for extra in ("data/raw/osm_courts_nv.csv",):
        if Path(extra).exists():
            con.execute(f"insert into pins select lat, lon from read_csv_auto('{extra}') where lat is not null and lon is not null")
    con.execute(f"""create table cells as
        select distinct cx + dx as cx, cy + dy as cy
        from (select cast(floor(lon * {CELLS_PER_DEGREE}) as integer) as cx, cast(floor(lat * {CELLS_PER_DEGREE}) as integer) as cy from pins) c,
             (select unnest([-1, 0, 1]) as dx), (select unnest([-1, 0, 1]) as dy)""")
    print(f"{con.execute('select count(*) from pins').fetchone()[0]:,} pins, {con.execute('select count(*) from cells').fetchone()[0]:,} cells")

    con.execute('set threads=8')
    path = f"s3://{BUCKET}/release/{release}/theme=addresses/type=address/*"
    con.execute(f"""
        copy (
            select a.id as address_id, a.number as house_number, a.street, a.unit, a.postcode,
                   coalesce(a.postal_city, a.address_levels[2].value) as city, a.address_levels[1].value as state,
                   a.bbox.ymin as lat, a.bbox.xmin as lon, '{release}' as release
            from read_parquet('{path}', hive_partitioning=1) a
            join cells c on c.cx = cast(floor(a.bbox.xmin * {CELLS_PER_DEGREE}) as integer)
                        and c.cy = cast(floor(a.bbox.ymin * {CELLS_PER_DEGREE}) as integer)
            where a.bbox.xmin between -124.5 and -114.0 and a.bbox.ymin between 32.5 and 42.1
              and a.country = 'US' and a.number is not null and a.street is not null
        ) to '{args.out}' (header, delimiter ',')""")
    n = con.execute(f"select count(*) from read_csv_auto('{args.out}')").fetchone()[0]
    print(f"Wrote {n:,} address points to {args.out}")


if __name__ == "__main__":
    main()
