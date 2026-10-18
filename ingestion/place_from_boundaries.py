"""City fill by boundary lookup (docs/sessions/2026-10-17-city-fill-last-94.md follow-up).

For pins that still have no city after every other source in `int_venue_address`, find the US Census place (incorporated city or
census-designated place) whose boundary contains the pin; if none does, the county. Results go to transform/seeds/venue_place_boundary.csv
(one row per pin, lat/lon = the pin looked up), so the dbt model needs no spatial SQL and CI needs no boundary data.

The boundaries are the reference table raw.census_boundaries (Census 2023, public domain; `ingestion/extract_census_boundaries.py` writes
data/raw/census_boundaries.csv, `make load` loads it). Nothing is downloaded here.

    python ingestion/place_from_boundaries.py

Needs a built courtconnect.duckdb with raw.census_boundaries loaded, and DuckDB's spatial extension (INSTALL spatial). A pin that moved gets
a new row; rows for pins that now have a city from elsewhere stay harmless (the model reads them only for pins still cityless). Seeds keep CRLF.
"""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "transform" / "seeds" / "venue_place_boundary.csv"
FIELDS = ["venue_id", "lat", "lon", "place_name", "place_kind", "source", "checked_on"]
SOURCE = "US Census cartographic boundary files 2023 (1:500k)"


def main() -> None:
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
    if not pins:
        return
    con.execute("create temp table pin (venue_id varchar, lat double, lon double)")
    con.executemany("insert into pin values (?, ?, ?)", pins)
    con.execute("create temp table pin_geom as select *, st_point(lon, lat) as g from pin")
    con.execute("create temp table shape as select kind, state_fips, name, st_geomfromtext(wkt) as geom from raw.census_boundaries")
    if not con.execute("select count(*) from shape").fetchone()[0]:
        raise SystemExit("raw.census_boundaries is empty: run extract_census_boundaries.py, then load_raw.py")
    found: dict[str, tuple[str, str]] = {}
    for vid, name in con.execute(
        "select p.venue_id, s.name from pin_geom p join shape s on s.kind = 'place' and st_contains(s.geom, p.g)"
    ).fetchall():
        found[vid] = (name, "place")
    for vid, name in con.execute(
        "select p.venue_id, s.name from pin_geom p join shape s on s.kind = 'county' and st_contains(s.geom, p.g)"
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
    main()
