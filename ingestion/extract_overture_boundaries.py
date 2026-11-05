"""Extract Mexican municipality + locality boundaries from Overture divisions as a reference table (raw.census_boundaries, ADR 0034).

Overture's `divisions` theme (CDLA-Permissive, same S3 bucket and release as the places) has a polygon per Mexican municipio
(subtype `county`, 2,475 of them, so every pin falls in one) and per named locality (subtype `locality`, 1,602, sparse: Tijuana
itself has none, only its municipio). Same shape as the US file so `place_from_boundaries.py` reads both:
kind `place` = locality, kind `county` = municipio (the "Municipio de " prefix is dropped), state_fips = the ISO 3166-2 state code
(MX-BCN) instead of a Census FIPS, geoid = the Overture division id. Land areas only, simplified to about 100 m.

    python ingestion/extract_overture_boundaries.py                  # newest release, all of Mexico
    python ingestion/extract_overture_boundaries.py --release 2026-10-21.0

Output: data/raw/census_boundaries_mx.csv (`make load` appends it to raw.census_boundaries, like the per-state extras of the other
raw files). Needs DuckDB's spatial extension and network access (range reads of the public bucket; no API key).
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import duckdb

from extract_overture_places import BUCKET, latest_release
from rawdir import raw_path

SIMPLIFY_DEG = 0.001   # about 100 m; the US files are 1:500k
COUNTRY = "MX"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--release", default=None)
    ap.add_argument("--out", default=raw_path(f"census_boundaries_{COUNTRY.lower()}.csv"))
    args = ap.parse_args()
    release = args.release or latest_release()
    print(f"Overture release {release}")

    con = duckdb.connect()
    con.execute("install httpfs; load httpfs; set s3_region='us-west-2';")
    try:
        con.execute("load spatial")
    except duckdb.Error:
        con.execute("install spatial")
        con.execute("load spatial")
    path = f"s3://{BUCKET}/release/{release}/theme=divisions/type=division_area/*"
    source = f"Overture Maps divisions {release} (CDLA-Permissive), simplified to ~100 m"
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"""
        copy (
            select case subtype when 'locality' then 'place' else 'county' end as kind,
                   region as state_fips, division_id as geoid,
                   trim(regexp_replace(names.primary, '^Municipio de ', '')) as name,
                   st_astext(st_simplifypreservetopology(geometry, {SIMPLIFY_DEG})) as wkt,
                   '{source}' as source, '{date.today().isoformat()}' as extracted_at
            from read_parquet('{path}', hive_partitioning=1)
            where country = '{COUNTRY}' and class = 'land' and subtype in ('locality', 'county')
              and names.primary is not null and region is not null
            order by kind, state_fips, geoid
        ) to '{out.as_posix()}' (header, delimiter ',')""")
    n = con.execute(f"select kind, count(*) from read_csv_auto('{out.as_posix()}') group by 1 order by 1").fetchall()
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB): {n}")


if __name__ == "__main__":
    main()
