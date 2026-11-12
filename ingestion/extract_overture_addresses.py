"""Extract Overture address points that sit near a map pin, for the address fill (docs/ml.md, tier 2).

Overture publishes every address point it knows (open data, same release as the places we load). We only need the ones
within ~150 m of a pin, so this reads the pin coordinates from data/raw (OSM courts, Overture places) and
seeds/manual_venues.csv, and keeps address points in the 1-cell neighbourhood (0.004 deg, ~440 m) of any pin. dbt picks the
nearest one within 150 m (int_venue_address). No API calls: DuckDB range requests against the public S3 bucket.

    python ingestion/extract_overture_addresses.py                    # newest release
    python ingestion/extract_overture_addresses.py --release 2026-09-23.1
    python ingestion/extract_overture_addresses.py --region HI        # one state only: replaces the cells around its pins

With --region CODE only the pins of that region (the `region` column of each pin source) set the cells: the address
points in those cells are replaced in the existing file and every other row stays as it is, so a new state skips the
full rewrite. Run extract_overture_places.py --region CODE first (its places are pins too).

Output: data/raw/overture_addresses.csv (load_raw.py loads it into raw.overture_addresses; CI uses a fixture).
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import duckdb

import overpass
from extract_overture_places import BUCKET, latest_release
from rawdir import raw_path

CELLS_PER_DEGREE = 250   # 0.004 deg cells


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--release", default=None)
    ap.add_argument("--out", default=raw_path("overture_addresses.csv"))
    ap.add_argument("--region", default=None, choices=sorted(overpass.REGIONS),
                    help="only the pins of this region; replace those cells in the existing file (default: all, rewrite)")
    args = ap.parse_args()
    release = args.release or latest_release()
    print(f"Overture release {release}")

    con = duckdb.connect()
    con.execute("install httpfs; load httpfs; set s3_region='us-west-2';")
    src = [raw_path("osm_courts.csv"), raw_path("overture_places.csv"), "transform/seeds/manual_venues.csv"]
    src += [p.as_posix() for p in sorted(Path(raw_path("")).glob("osm_courts_??.csv"))]   # one file per extra state (overpass.out_name)
    con.execute("create table pins (lat double, lon double)")
    for f in src:
        # --region: only that region's pins (every pin source has a region column; manual venues may leave it blank)
        where = f"and region = '{args.region}'" if args.region else ""
        con.execute(f"insert into pins select lat, lon from read_csv_auto('{f}') where lat is not null and lon is not null {where}")
    con.execute(f"""create table cells as
        select distinct cx + dx as cx, cy + dy as cy
        from (select cast(floor(lon * {CELLS_PER_DEGREE}) as integer) as cx, cast(floor(lat * {CELLS_PER_DEGREE}) as integer) as cy from pins) c,
             (select unnest([-1, 0, 1]) as dx), (select unnest([-1, 0, 1]) as dy)""")
    print(f"{con.execute('select count(*) from pins').fetchone()[0]:,} pins, {con.execute('select count(*) from cells').fetchone()[0]:,} cells")

    con.execute('set threads=8')
    path = f"s3://{BUCKET}/release/{release}/theme=addresses/type=address/*"
    if args.region:   # this region's box plus a margin for the 1-cell neighbourhood: lets the parquet reader skip most row groups
        s, w, n, e = overpass.REGIONS[args.region]["bbox"]
        m = 0.01
        bbox_sql = f"a.bbox.xmin between {w - m} and {e + m} and a.bbox.ymin between {s - m} and {n + m}"
    else:
        bbox_sql = overpass.sql_bbox('a.bbox.xmin', 'a.bbox.ymin')
    # the region's country (regions.json, default US); with no --region the countries of every non-deferred region
    countries = ", ".join(sorted({f"'{cfg['country']}'" for code, cfg in overpass.REGIONS.items() if args.region == code or (not args.region and not cfg['defer'])}))
    fetched = f"""
            select a.id as address_id, a.number as house_number, a.street, a.unit, a.postcode,
                   coalesce(a.postal_city, a.address_levels[2].value) as city, a.address_levels[1].value as state,
                   a.bbox.ymin as lat, a.bbox.xmin as lon, '{release}' as release
            from read_parquet('{path}', hive_partitioning=1) a
            join cells c on c.cx = cast(floor(a.bbox.xmin * {CELLS_PER_DEGREE}) as integer)
                        and c.cy = cast(floor(a.bbox.ymin * {CELLS_PER_DEGREE}) as integer)
            where {bbox_sql}
              and a.country in ({countries}) and a.number is not null and a.street is not null
              and (a.country = 'US' or coalesce(a.sources[1].license, '') not ilike '%proprietary%')   -- ADR 0034: Mexico's mx/countrywide is tagged LicenseRef-Proprietary, so its points are not kept"""
    out = Path(args.out)
    if args.region and out.exists():
        # keep every existing row outside this region's cells, add the freshly read ones (same cells, so no duplicates)
        con.execute(f"create table fresh as {fetched}")
        con.execute(f"""copy (
            select * from read_csv_auto('{out.as_posix()}', all_varchar=true)
            where not exists (select 1 from cells c where c.cx = cast(floor(cast(lon as double) * {CELLS_PER_DEGREE}) as integer)
                                                      and c.cy = cast(floor(cast(lat as double) * {CELLS_PER_DEGREE}) as integer))
            union all select columns(*)::varchar from fresh) to '{out.as_posix()}.new' (header, delimiter ',')""")
        os.replace(f"{out}.new", out)
    else:
        con.execute(f"copy ({fetched}) to '{out.as_posix()}' (header, delimiter ',')")
    n = con.execute(f"select count(*) from read_csv_auto('{out.as_posix()}')").fetchone()[0]
    print(f"Wrote {n:,} address points to {args.out}")


if __name__ == "__main__":
    main()
