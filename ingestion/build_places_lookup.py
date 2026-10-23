"""Build app/data/places.json: every California + Nevada Census place (city, town or CDP) as [name, state, lat, lon], so the map search can centre on a city that has no venue pins yet.

Source: US Census Bureau 2023 Gazetteer, places file (public domain), downloaded to a temp folder and deleted:
https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_place_national.zip

    python ingestion/build_places_lookup.py

The Gazetteer names carry a legal suffix ("Truckee town", "Fresno city", "Alpine CDP"); it is dropped. The point is the Census internal point (INTPTLAT/INTPTLONG), not a city hall.
Output: app/data/places.json, a JSON list sorted by name (about 70 KB), lazy-loaded by app/index.html only when a typed city matches no venue. Needs network access; run it rarely (the Gazetteer changes once a year).
"""
from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from pathlib import Path

import requests

from useragent import HEADERS as UA

URL = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_place_national.zip"
STATES = {"CA", "NV"}
SUFFIX = re.compile(r"\s+(city|town|village|borough|municipality|CDP|city and borough|urban county|consolidated government \(balance\)|metropolitan government \(balance\)|unified government \(balance\))$", re.I)
OUT = Path(__file__).resolve().parent.parent / "app" / "data" / "places.json"


def main() -> None:
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
    places = sorted(out.values(), key=lambda p: (p[0].lower(), p[1]))
    OUT.write_text(json.dumps(places, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    print(f"{len(places)} places -> {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
