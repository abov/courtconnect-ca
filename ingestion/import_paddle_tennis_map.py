"""Turn the hand-compiled "Pop Tennis West LA" Google My Map into rows for transform/seeds/manual_venues.csv.

The map's owner shares it as a link; its KML export lists each court's Type (Public / Private / ?), address, court count and rules,
but NO coordinates (Google places the pins at display time). So positions come from OpenStreetMap's geocoder (Nominatim),
refined to the OpenStreetMap park outline when the geocoder only found a street, and every row records how it was placed.

Only Public and "?" (access in question) entries are imported. Private entries, including private homes, are deliberately skipped.

    python ingestion/import_paddle_tennis_map.py            # dry run: print what would be written
    python ingestion/import_paddle_tennis_map.py --write    # replace the 'pt-*' rows in manual_venues.csv

Needs PADDLE_TENNIS_MAP_ID in .env (the `mid=` value of the map's link). Review the output before committing.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import time
import xml.etree.ElementTree as ET

import duckdb
import requests
from dotenv import load_dotenv

NS = {"k": "http://www.opengis.net/kml/2.2"}
UA = {"User-Agent": "courtconnect-ca/0.1 (portfolio project)"}
SEED = "transform/seeds/manual_venues.csv"
COLS = ["venue_key", "venue_name", "sport", "city", "lat", "lon", "location_precision", "website", "surface_type", "setting", "offerings",
        "courts", "access", "rules", "evidence"]
# map name -> OpenStreetMap park name, used when the geocoder could only place a street
PARK_HINT = {"Glen Alla Park": "Glen Alla Park", "Fox Hills Park": "Fox Hills Park", "Oberrieder Park Paddle Tennis Courts": "Oberrieder Park",
             "Syd Kronenthal Park": "Syd Kronenthal Park", "Ladera Linda Community Park": "Ladera Linda Park"}
NAME_FIX = {"Tennis Courts": "Tennis Courts (49 Seawall Rd)"}


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def fetch_selected(map_id: str) -> list[dict]:
    r = requests.get("https://www.google.com/maps/d/kml", params={"mid": map_id, "forcekml": 1}, timeout=60, headers=UA)
    r.raise_for_status()
    doc = ET.fromstring(r.content).find("k:Document", NS)
    rows = []
    for pm in doc.iter("{http://www.opengis.net/kml/2.2}Placemark"):
        ext = {d.get("name"): (d.findtext("k:value", namespaces=NS) or "").strip() for d in pm.findall(".//k:Data", NS)}
        if ext.get("Type") in ("Public", "?"):
            rows.append({"name": (pm.findtext("k:name", namespaces=NS) or "").strip(), **ext})
    return rows


def geocode(row: dict):
    addr = row["Address"].replace("CA CA", "CA")
    m = re.search(r",\s*([^,]+),\s*CA", addr)
    city = m.group(1).strip() if m else ""
    tries = [addr, f'{row["name"]}, {city}, California']
    if "&" in addr.split(",")[0]:
        tries.insert(1, f'{addr.split(",")[0].split("&")[0].strip()}, {city}, California')
    for q in tries:
        res = requests.get("https://nominatim.openstreetmap.org/search", headers=UA, timeout=30,
                           params={"q": q, "format": "jsonv2", "limit": 1, "countrycodes": "us"}).json()
        time.sleep(1.2)                                                     # Nominatim usage policy: 1 request per second
        if res and city.lower().split()[0] in res[0]["display_name"].lower():
            return float(res[0]["lat"]), float(res[0]["lon"]), q, city
    return None, None, "", city


def main() -> None:
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--db", default="courtconnect.duckdb")
    args = ap.parse_args()
    map_id = os.environ.get("PADDLE_TENNIS_MAP_ID", "").strip()
    if not map_id:
        sys.exit("PADDLE_TENNIS_MAP_ID is not set (the mid= value in the map's link). Put it in .env.")

    parks = {}
    if os.path.exists(args.db):
        con = duckdb.connect(args.db, read_only=True)
        parks = {r[0]: (r[1], r[2]) for r in con.execute(
            "select parent_name, (minlat+maxlat)/2, (minlon+maxlon)/2 from staging.stg_osm_parents").fetchall()}

    out = []
    for r in fetch_selected(map_id):
        lat, lon, via, city = geocode(r)
        precision = None
        street_only = (not via) or (via.endswith("California") and not re.search(r"\d", via.split(",")[0]))
        if street_only and PARK_HINT.get(r["name"]) in parks:
            lat, lon = parks[PARK_HINT[r["name"]]]
            precision = "park centre (OpenStreetMap park outline)"
        if lat is None:
            print(f'  SKIPPED (could not place): {r["name"]}', file=sys.stderr)
            continue
        if precision is None:
            if re.search(r"\d", via.split(",")[0]):
                precision = "address (OpenStreetMap geocoder)"
            elif via.startswith(r["name"]):
                precision = "place name (OpenStreetMap geocoder)"
            else:
                precision = "street only (approximate)"
        access = "public" if r["Type"] == "Public" else "unknown"
        note = ("Type = Public. " if access == "public" else "Type marked '?', so public access is NOT confirmed. ")
        out.append({"venue_key": "pt-" + slug(r["name"]), "venue_name": NAME_FIX.get(r["name"], r["name"]), "sport": "Pop Tennis", "city": city,
                    "lat": f"{lat:.5f}", "lon": f"{lon:.5f}", "location_precision": precision, "website": "", "surface_type": "unknown",
                    "setting": "unknown", "offerings": "", "courts": str(int(float(r["Count"]))) if r.get("Count") else "", "access": access,
                    "rules": r.get("Rules", "") or "",
                    "evidence": f"Pop Tennis West LA map (compiled by the project owner): {note}Address on the map: "
                                f"{r['Address'].replace('CA CA', 'CA')}. Location placed with the OpenStreetMap geocoder: {precision}."})
    for o in out:
        print(f'{o["access"]:8s} {o["venue_name"][:38]:38s} {o["lat"]},{o["lon"]}  {o["location_precision"]}')
    print(f"{len(out)} venues (Public + ? only)")
    if not args.write:
        print("dry run; add --write to update", SEED)
        return
    with open(SEED, encoding="utf-8", newline="") as f:
        keep = [r for r in csv.DictReader(f) if not r["venue_key"].startswith("pt-")]
    with open(SEED, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(keep + out)
    print("wrote", SEED)


if __name__ == "__main__":
    main()
