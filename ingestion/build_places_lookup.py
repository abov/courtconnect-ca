"""Build app/data/places.json: every California + Nevada Census place (city, town or CDP) as [name, state, lat, lon], so the map search can centre on a city that has no venue pins yet.

Source: US Census Bureau 2023 Gazetteer, places file (public domain), downloaded to a temp folder and deleted:
https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_place_national.zip

    python ingestion/build_places_lookup.py

The Gazetteer names carry a legal suffix ("Truckee town", "Fresno city", "Alpine CDP"); it is dropped. The point is the Census internal point (INTPTLAT/INTPTLONG), not a city hall.
Mexico (ADR 0034): `python ingestion/build_places_lookup.py --mx` (offline) replaces the MX rows with the border-pilot cities below, each a city-centre point that must fall inside the Overture
municipio or locality of the same name in census_boundaries_mx.csv in the shared raw folder (a municipio's own centroid is far from its city: Tijuana's is 20 km south). A plain run keeps the MX rows.
Output: app/data/places.json, a JSON list sorted by name (about 70 KB), lazy-loaded by app/index.html only when a typed city matches no venue. Needs network access; run it rarely (the Gazetteer changes once a year).
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
import zipfile
from pathlib import Path

import requests

import rawdir
from overpass import REGIONS
from useragent import HEADERS as UA

URL = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_place_national.zip"
STATES = set(REGIONS)  # region codes from ingestion/regions.json
SUFFIX = re.compile(r"\s+(city|town|village|borough|municipality|CDP|city and borough|urban county|consolidated government \(balance\)|metropolitan government \(balance\)|unified government \(balance\))$", re.I)
OUT = Path(__file__).resolve().parent.parent / "app" / "data" / "places.json"
# Border-pilot cities (docs/decisions/0034-mexico-scope.md): (display name, boundary name in the Overture file, city-centre lat, lon). Only the pilot's: other Mexican cities stay out until their metro starts.
MX_CITIES = [("Tijuana", "Tijuana", 32.515, -117.038), ("Tecate", "Tecate", 32.572, -116.626), ("Playas de Rosarito", "Playas de Rosarito", 32.361, -117.057),
             ("Rosarito", "Playas de Rosarito", 32.361, -117.057), ("Mexicali", "Mexicali", 32.624, -115.452), ("Ensenada", "Ensenada", 31.867, -116.596),
             ("Hermosillo", "Hermosillo", 29.073, -110.956), ("Nogales", "Nogales", 31.309, -110.946), ("San Luis Río Colorado", "San Luis Río Colorado", 32.456, -114.772)]


def mx_places() -> list:
    """The pilot cities as [name, "MX", lat, lon]; stops if a point is not inside the named Overture municipio or locality (spatial extension of DuckDB)."""
    import duckdb
    con = duckdb.connect()
    try:
        con.execute("load spatial")
    except duckdb.Error:
        con.execute("install spatial")
        con.execute("load spatial")
    con.execute("create table b as select name, st_geomfromtext(wkt) g from read_csv(?) where state_fips like 'MX-%'", [str(rawdir.raw_dir() / "census_boundaries_mx.csv").replace("\\", "/")])
    out = []
    for name, shape, lat, lon in MX_CITIES:
        if not con.execute("select count(*) from b where name = ? and st_contains(g, st_point(?, ?))", [shape, lon, lat]).fetchone()[0]:
            raise SystemExit(f"{name}: ({lat}, {lon}) is not inside the Overture shape '{shape}'")
        out.append([name, "MX", lat, lon])
    return out


def write(places: list) -> None:
    places = sorted(places, key=lambda p: (p[0].lower(), p[1]))
    OUT.write_text(json.dumps(places, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    print(f"{len(places)} places -> {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")


def main() -> None:
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else []
    if "--mx" in sys.argv:
        write([p for p in old if p[1] != "MX"] + mx_places())
        return
    r = requests.get(URL, headers=UA, timeout=120)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        name = next(n for n in z.namelist() if n.endswith(".txt"))
        text = z.read(name).decode("utf-8-sig")
    rows = csv.reader(io.StringIO(text), delimiter="\t")
    head = [h.strip() for h in next(rows)]
    ix = {h: head.index(h) for h in ("USPS", "NAME", "INTPTLAT", "INTPTLONG")}
    out = {}
    for row in rows:
        if row[ix["USPS"]] not in STATES:
            continue
        nm = SUFFIX.sub("", row[ix["NAME"]].strip())
        key = (nm.lower(), row[ix["USPS"]])
        out.setdefault(key, [nm, row[ix["USPS"]], round(float(row[ix["INTPTLAT"]]), 3), round(float(row[ix["INTPTLONG"]]), 3)])
    write(list(out.values()) + [p for p in old if p[1] == "MX"])


if __name__ == "__main__":
    main()
