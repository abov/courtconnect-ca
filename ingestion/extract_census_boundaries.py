"""Extract US Census place + county boundaries for CA and NV as a reference table (raw.census_boundaries).

Source: US Census Bureau cartographic boundary files, 2023, 1:500k (public domain), from
https://www2.census.gov/geo/tiger/GENZ2023/shp/ : cb_2023_06_place_500k, cb_2023_32_place_500k, cb_2023_us_county_500k (~13 MB in all).
"place" = incorporated cities and census-designated places. Boundaries change about once a year, so this runs rarely (not in the monthly extract).

    python ingestion/extract_census_boundaries.py

Output: data/raw/census_boundaries.csv, one row per shape: kind (place|county), state_fips, geoid, name, wkt (WGS84 polygon), source, extracted_at.
`make load` puts it in raw.census_boundaries; `ingestion/place_from_boundaries.py` reads it to name the city of a pin nothing else places.
Needs DuckDB's spatial extension (INSTALL spatial) and network access. The zips are downloaded to a temp folder and deleted.
"""
from __future__ import annotations

import sys
import tempfile
from datetime import date
from pathlib import Path

import duckdb
import requests

from rawdir import raw_path

BASE = "https://www2.census.gov/geo/tiger/GENZ2023/shp/"
UA = {"User-Agent": "courtconnect-ca/0.1 (+https://github.com/abov/courtconnect-ca)"}
FILES = [("place", "cb_2023_06_place_500k"), ("place", "cb_2023_32_place_500k"), ("county", "cb_2023_us_county_500k")]
SOURCE = "US Census cartographic boundary files 2023 (1:500k)"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    con = duckdb.connect()
    try:
        con.execute("load spatial")
    except duckdb.Error:
        con.execute("install spatial")
        con.execute("load spatial")
    con.execute("create table shapes (kind varchar, state_fips varchar, geoid varchar, name varchar, wkt varchar)")
    with tempfile.TemporaryDirectory() as tmp:
        for kind, stem in FILES:
            z = Path(tmp) / f"{stem}.zip"
            r = requests.get(BASE + f"{stem}.zip", headers=UA, timeout=120)
            r.raise_for_status()
            z.write_bytes(r.content)
            print(f"{stem}: {len(r.content) / 1e6:.1f} MB")
            con.execute(
                f"""insert into shapes
                    select '{kind}', STATEFP, GEOID, NAME, st_astext(geom) from st_read('/vsizip/{z.as_posix()}')
                    where STATEFP in ('06', '32')"""
            )
    out = Path(raw_path("census_boundaries.csv"))
    out.parent.mkdir(parents=True, exist_ok=True)
    con.execute(
        f"""copy (select kind, state_fips, geoid, name, wkt, '{SOURCE}' as source, '{date.today().isoformat()}' as extracted_at
                  from shapes order by kind, state_fips, geoid) to '{out.as_posix()}' (header, delimiter ',')"""
    )
    n = con.execute("select kind, count(*) from shapes group by 1 order by 1").fetchall()
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB): {n}")


if __name__ == "__main__":
    main()
