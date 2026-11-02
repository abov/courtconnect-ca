"""Build app/data/zips.json: every ZIP code area (Census ZCTA) whose centre lies inside a covered state, as {"zip": [lat, lon]}, so the map search can centre on a typed ZIP.

Source: US Census Bureau 2023 Gazetteer, ZCTA file (public domain), downloaded to memory:
https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_zcta_national.zip

    python ingestion/build_zips_lookup.py

The point is the Census internal point (INTPTLAT/INTPTLONG). A ZCTA belongs to a state when that point lies inside the state border polygon
(ingestion/regions.json), so a ZIP area that straddles a border goes to the state its centre is in. Output: app/data/zips.json (about 50-80 KB),
lazy-loaded by app/index.html when someone types a ZIP. Needs network access; run it when a state is added (the Gazetteer changes once a year).
"""
from __future__ import annotations

import csv
import io
import json
import zipfile
from pathlib import Path

import requests

from overpass import region_at
from useragent import HEADERS as UA

URL = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_zcta_national.zip"
OUT = Path(__file__).resolve().parent.parent / "app" / "data" / "zips.json"


def main() -> None:
    r = requests.get(URL, headers=UA, timeout=120)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        name = next(n for n in z.namelist() if n.endswith(".txt"))
        text = z.read(name).decode("utf-8-sig")
    rows = csv.reader(io.StringIO(text), delimiter="\t")
    head = [h.strip() for h in next(rows)]
    ix = {h: head.index(h) for h in ("GEOID", "INTPTLAT", "INTPTLONG")}
    out = {}
    for row in rows:
        lat, lon = round(float(row[ix["INTPTLAT"]]), 3), round(float(row[ix["INTPTLONG"]]), 3)
        if region_at(lat, lon):
            out[row[ix["GEOID"]]] = [lat, lon]
    out = dict(sorted(out.items()))
    OUT.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    print(f"{len(out)} ZIP areas -> {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
