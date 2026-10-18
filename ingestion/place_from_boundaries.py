"""City fill by boundary lookup (docs/sessions/2026-10-17-city-fill-last-94.md follow-up).

For pins that still have no city after every other source in `int_venue_address`, find the US Census place (incorporated city or
census-designated place) whose boundary contains the pin; if none does, the county. Results go to transform/seeds/venue_place_boundary.csv
(one row per pin, lat/lon = the pin looked up), so the dbt model needs no spatial SQL and CI needs no shapefiles.

Source: US Census Bureau cartographic boundary files (public domain), 2023, 1:500k:
  cb_2023_06_place_500k.zip, cb_2023_32_place_500k.zip, cb_2023_us_county_500k.zip
  from https://www2.census.gov/geo/tiger/GENZ2023/shp/ . Download them into a folder and pass it as the argument.

    python ingestion/place_from_boundaries.py <folder with the three zips>

Needs a built courtconnect.duckdb and DuckDB's spatial extension (INSTALL spatial). Existing rows for pins that moved are replaced; rows for
pins that now have a city from elsewhere stay harmless (the model only reads them for pins that are still cityless). Seeds keep CRLF.
"""
from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "transform" / "seeds" / "venue_place_boundary.csv"
FIELDS = ["venue_id", "lat", "lon", "place_name", "place_kind", "source", "checked_on"]
SOURCE = "US Census cartographic boundary files 2023 (1:500k)"
STATE_FIPS = {"CA": "06", "NV": "32"}


def main(folder: Path) -> None:
    con = duckdb.connect(str(ROOT / "courtconnect.duckdb"), read_only=True)
    try:
        con.execute("load spatial")
    except duckdb.Error:
        con.execute("install spatial")
        con.execute("load spatial")
    pins = con.execute(
        """select a.venue_id, v.lat, v.lon from intermediate.int_venue_address a join core.dim_venue v using (venue_id)
           where (a.city is null or trim(a.city) = '') and v.lat is not null and v.lon is not null"""
    ).fetchall()
    print(f"{len(pins)} pins still have no city")
    con.execute("create temp table pin (venue_id varchar, lat double, lon double)")
    con.executemany("insert into pin values (?, ?, ?)", pins)
    con.execute("create temp table pin_geom as select *, st_point(lon, lat) as g from pin")
    found: dict[str, tuple[str, str]] = {}
    for fips in STATE_FIPS.values():
        z = (folder / f"cb_2023_{fips}_place_500k.zip").as_posix()
        for vid, name in con.execute(
            f"select p.venue_id, s.NAME from pin_geom p join st_read('/vsizip/{z}') s on st_contains(s.geom, p.g)"
        ).fetchall():
            found[vid] = (name, "place")
    z = (folder / "cb_2023_us_county_500k.zip").as_posix()
    for vid, name in con.execute(
        f"select p.venue_id, s.NAME from pin_geom p join st_read('/vsizip/{z}') s on st_contains(s.geom, p.g) where s.STATEFP in ('06','32')"
    ).fetchall():
        found.setdefault(vid, (f"{name} County", "county"))
    old = {}
    if SEED.exists():
        with SEED.open(newline="", encoding="utf-8") as f:
            old = {r["venue_id"]: r for r in csv.DictReader(f)}
    today = date.today().isoformat()
    for vid, lat, lon in pins:
        if vid in found:
            name, kind = found[vid]
            old[vid] = {"venue_id": vid, "lat": round(lat, 6), "lon": round(lon, 6), "place_name": name, "place_kind": kind,
                        "source": SOURCE, "checked_on": today}
    with SEED.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\r\n")
        w.writeheader()
        w.writerows(sorted(old.values(), key=lambda r: r["venue_id"]))
    kinds = [k for _, k in found.values()]
    print(f"place {kinds.count('place')}, county only {kinds.count('county')}, none {len(pins) - len(found)}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
