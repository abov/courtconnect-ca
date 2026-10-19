"""Compare the City of LA Recreation and Parks facility scan with the map and list the gaps.

    1. Run ingestion/la_recreation_scan.js in the Browser pane (the site answers 403 to scripts) and save its CSV as
       ingestion/data/la_recreation_scan.csv.
    2. python ingestion/la_recreation_scan.py [--radius-m 400]

Coordinates and names come from the city's own open-data list "LAPARKS.ORG Recreation and Parks Facilities"
(data.lacity.org/resource/ukgg-rgf9), joined on the page slug. The scan only says a site LISTS "Tennis Courts", "Handball Courts",
"Pickleball" or "Paddle Tennis"; it gives no court count and no wall count. A site counts as already on the map when a pin of the
right kind sits within --radius-m of the park point (parks are big and the open-data point is a centre, so keep this generous).
Reads app/data/venues.json (the committed export), so no database is needed. Prints the gaps; seed them by hand with the page URL as evidence.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = "courtconnect-ca/0.1 (+https://github.com/abov/courtconnect-ca)"
OPEN_DATA = "https://data.lacity.org/resource/ukgg-rgf9.json?$limit=5000"
SITE = "https://recreation.parks.lacity.gov"

# page feature -> (label, venue sport names that count as already mapped; None = check the walls layer instead)
KINDS = {
    "tennis": ("Tennis Courts", re.compile(r"^tennis courts?\b", re.I), {"Tennis"}),
    "handball": ("Handball Courts", re.compile(r"^handball court", re.I), None),
    "pickleball": ("Pickleball", re.compile(r"^pickleball", re.I), {"Pickleball"}),
    "paddle": ("Paddle Tennis", re.compile(r"paddle", re.I), {"Pop Tennis", "Paddle Tennis"}),
    "racquetball": ("Racquetball Courts", re.compile(r"^racquetball", re.I), {"Racquetball"}),
}


def metres(lat1, lon1, lat2, lon2):
    dy = (lat2 - lat1) * 111_320
    dx = (lon2 - lon1) * 111_320 * math.cos(math.radians((lat1 + lat2) / 2))
    return math.hypot(dx, dy)


def open_data_by_slug():
    req = urllib.request.Request(OPEN_DATA, headers={"User-Agent": UA})
    rows = json.load(urllib.request.urlopen(req, timeout=60))
    out = {}
    for r in rows:
        url = (r.get("website") or {}).get("url", "")
        slug = url.rstrip("/").rsplit("/", 1)[-1]
        if slug and r.get("geolat") and r.get("geolong"):
            out.setdefault(slug, (r["locationname"].title(), r.get("address", ""), float(r["geolat"]), float(r["geolong"])))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--scan", default=str(ROOT / "ingestion/data/la_recreation_scan.csv"))
    ap.add_argument("--radius-m", type=float, default=400)
    args = ap.parse_args()

    app = json.load(open(ROOT / "app/data/venues.json", encoding="utf-8"))
    sport_names = [s["n"] for s in app["sports"]]
    venues = [(v["y"], v["x"], {sport_names[p[0]] for p in v["p"]}) for v in app["venues"]]
    walls = [(w["y"], w["x"]) for w in app["walls"]]
    places = open_data_by_slug()

    scan = list(csv.DictReader(open(args.scan, encoding="utf-8")))
    print(f"{len(scan)} pages list a racket-sport feature (the scan keeps only those)")
    gaps, nocoord, covered = [], [], {k: 0 for k in KINDS}
    for r in scan:
        slug = r["path"].rstrip("/").rsplit("/", 1)[-1]
        feats = [f for f in r["racket_features"].split(" | ") if f]
        for key, (label, pat, sports) in KINDS.items():
            hit = next((f for f in feats if pat.search(f)), None)
            if not hit:
                continue
            if slug not in places:
                nocoord.append((key, r["path"]))
                continue
            name, addr, lat, lon = places[slug]
            if sports is None:
                near = [m for m in (metres(lat, lon, y, x) for y, x in walls) if m <= args.radius_m]
            else:
                near = [m for m in (metres(lat, lon, y, x) for y, x, sp in venues if sp & sports) if m <= args.radius_m]
            if near:
                covered[key] += 1
            else:
                gaps.append((key, name, addr, lat, lon, hit, SITE + r["path"]))
    print("already on the map:", covered)
    print(f"\nGAPS ({len(gaps)}): site lists the facility, no pin of that kind within {args.radius_m:.0f} m")
    for g in sorted(gaps):
        print(" | ".join(str(x) for x in g))
    if nocoord:
        print(f"\nNO COORDINATES in the open-data list ({len(nocoord)}):")
        for k, p in nocoord:
            print(k, p)


if __name__ == "__main__":
    main()
