"""Subregion (Mexican federal entity) for every Mexican pin, by boundary lookup (ADR 0034).

For each pin with region MX, find the Overture municipio (raw.census_boundaries, kind `county`, state_fips = ISO 3166-2 code such as
MX-BCN) whose land polygon contains it; a pin just off the simplified coast takes the nearest municipio within about 5 km. Results go
to transform/seeds/venue_subregion.csv (one row per pin, lat/lon = the pin looked up), so the dbt model needs no spatial SQL and CI
needs no boundary data. `core.dim_venue.subregion` reads it, and only while the pin is still where it was looked up.

    python ingestion/subregion_from_boundaries.py

Needs a built courtconnect.duckdb with raw.census_boundaries loaded (`make load` appends census_boundaries_mx.csv) and DuckDB's spatial
extension. Run it after adding or moving Mexican pins, then rebuild. Nothing is downloaded. Seeds keep CRLF.
"""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "transform" / "seeds" / "venue_subregion.csv"
FIELDS = ["venue_id", "lat", "lon", "subregion", "source", "checked_on"]
NEAR_DEG = 0.05   # ~5 km: the municipio shapes are simplified land polygons, so a shore pin can fall just outside every one
SOURCE = "Overture Maps divisions municipio boundary (CDLA-Permissive)"


def main() -> None:
    con = duckdb.connect(str(ROOT / "courtconnect.duckdb"), read_only=True)
    try:
        con.execute("load spatial")
    except duckdb.Error:
        con.execute("install spatial")
        con.execute("load spatial")
    pins = con.execute("select venue_id, lat, lon from core.dim_venue where region = 'MX' and lat is not null and lon is not null").fetchall()
    print(f"{len(pins)} Mexican pins")
    if not pins:
        return
    con.execute("create temp table pin as select * from (values " + ",".join("(?, ?, ?)" for _ in pins) + ") t(venue_id, lat, lon)",
                [x for p in pins for x in p])
    con.execute("create temp table pin_geom as select *, st_point(lon, lat) as g from pin")
    con.execute("""create temp table shape as select state_fips as subregion, st_geomfromtext(wkt) as geom
                   from raw.census_boundaries where kind = 'county' and state_fips like 'MX-%'""")
    if not con.execute("select count(*) from shape").fetchone()[0]:
        raise SystemExit("no Mexican municipios in raw.census_boundaries: run extract_overture_boundaries.py, then load_raw.py")
    found = dict(con.execute("select p.venue_id, any_value(s.subregion) from pin_geom p join shape s on st_contains(s.geom, p.g) group by 1").fetchall())
    near = {}
    for vid, sub in con.execute(
        f"""select venue_id, arg_min(subregion, d) from (
                select p.venue_id, s.subregion, st_distance(s.geom, p.g) as d
                from pin_geom p join shape s on st_dwithin(s.geom, p.g, {NEAR_DEG})) group by venue_id"""
    ).fetchall():
        if vid not in found:
            near[vid] = sub
    today = date.today().isoformat()
    rows = []
    for vid, lat, lon in pins:
        sub = found.get(vid) or near.get(vid)
        if sub:
            rows.append({"venue_id": vid, "lat": round(lat, 6), "lon": round(lon, 6), "subregion": sub,
                         "source": SOURCE + (", nearest shape (pin just off the simplified coast)" if vid in near else ""), "checked_on": today})
    with SEED.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\r\n")
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: r["venue_id"]))
    print(f"inside a municipio {len(found)}, nearest shape {len(near)}, none {len(pins) - len(rows)} -> {SEED}")


if __name__ == "__main__":
    main()
