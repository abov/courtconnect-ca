"""Tier 3 of address fill (docs/ml_plan.md): reverse-geocode pins that still have no street address, via OSM's Nominatim.

Only NON-HOME pins with no address after tiers 1-2 (`int_venue_address`) are queried; home-like pins stay city-only (owner rule).
Results are cached in transform/seeds/nominatim_addresses.csv, one row per pin including misses, so a rerun never re-queries.

Nominatim usage policy (operations.osmfoundation.org/policies/nominatim): one request a second, a single thread, an identifying
User-Agent, results stored, no grid sweeps. This sends pin coordinates only (no email or other personal contact).

    python ingestion/reverse_geocode_blanks.py --limit 25     # query up to 25 uncached pins (sample); omit --limit for all
    python ingestion/reverse_geocode_blanks.py --dry-run      # count what would be queried
    python ingestion/reverse_geocode_blanks.py --cities       # CITY ONLY for any pin (home-like too) still without a city after every other source

A city names no street, so --cities also covers home-like pins. It asks Nominatim at town level (zoom 12) and stores the city on the pin's
cache row (a new row gets status 'city_only', which int_venue_address never uses for a street).

Needs a built courtconnect.duckdb (dbt build). Seeds keep CRLF line endings.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
import time
from datetime import date
from pathlib import Path

import duckdb
import requests

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "transform" / "seeds" / "nominatim_addresses.csv"
from useragent import HEADERS as UA
URL = "https://nominatim.openstreetmap.org/reverse"
FIELDS = ["venue_id", "lat", "lon", "status", "address_line", "city", "distance_m", "osm_ref", "queried_on"]   # lat/lon = the pin queried (a moved pin is re-queried and its old row ignored)
MAX_DISTANCE_M = 150   # same bound as the Overture tier: farther is not "nearest address" for these courts


def distance_m(lat1, lon1, lat2, lon2) -> float:
    return math.hypot((lat1 - lat2) * 110540, (lon1 - lon2) * math.cos(math.radians(lat1)) * 111320)


def load_cache() -> dict[str, dict]:
    if not SEED.exists():
        return {}
    with SEED.open(newline="", encoding="utf-8") as f:
        return {r["venue_id"]: r for r in csv.DictReader(f)}


def save_cache(cache: dict[str, dict]) -> None:
    with SEED.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\r\n")
        w.writeheader()
        for vid in sorted(cache):
            w.writerow(cache[vid])


def blanks() -> list[tuple]:
    con = duckdb.connect(str(ROOT / "courtconnect.duckdb"), read_only=True)
    # hash order = a fixed pseudo-random order, so a --limit sample mixes CA and NV and a rerun continues where it stopped
    return con.execute("""
        select a.venue_id, v.lat, v.lon, v.region
        from intermediate.int_venue_address a join core.dim_venue v using (venue_id)
        where a.address_line is null and not a.is_home_like and v.lat is not null and v.lon is not null
        order by hash(a.venue_id)
    """).fetchall()


def cityless() -> list[tuple]:
    con = duckdb.connect(str(ROOT / "courtconnect.duckdb"), read_only=True)
    return con.execute("""
        select a.venue_id, v.lat, v.lon from intermediate.int_venue_address a join core.dim_venue v using (venue_id)
        where (a.city is null or a.city = '') and v.lat is not null and v.lon is not null order by hash(a.venue_id)
    """).fetchall()


def city_of(addr: dict) -> str:
    return addr.get("city") or addr.get("town") or addr.get("village") or addr.get("hamlet") or addr.get("municipality") or addr.get("suburb") or ""


def lookup(lat: float, lon: float, zoom: int = 18) -> dict:
    r = requests.get(URL, headers=UA, timeout=30,
                     params={"lat": lat, "lon": lon, "format": "jsonv2", "zoom": zoom, "addressdetails": 1})
    r.raise_for_status()
    return r.json()


def fill_cities(cache: dict[str, dict], limit: int | None, dry_run: bool) -> None:
    todo = cityless()
    print(f"{len(todo)} pins still have no city ({len(cache)} cached rows)")
    if dry_run:
        return
    done = found = 0
    for vid, lat, lon in todo[:limit]:
        try:
            city = city_of(lookup(lat, lon, zoom=12).get("address", {}) or {})
        except requests.RequestException as e:
            print("stopping on error:", e, file=sys.stderr)
            break
        row = cache.get(vid) or {"venue_id": vid, "lat": round(lat, 6), "lon": round(lon, 6), "status": "city_only", "address_line": "", "city": "",
                                 "distance_m": "", "osm_ref": "", "queried_on": date.today().isoformat()}
        if city:
            row["city"] = city
            found += 1
        cache[vid] = row
        done += 1
        save_cache(cache)   # after every pin: an interrupted run loses nothing
        time.sleep(1.1)     # policy: at most 1 request per second
    print(f"queried {done}, city found for {found}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cities", action="store_true")
    args = ap.parse_args()
    cache = load_cache()
    if args.cities:
        return fill_cities(cache, args.limit, args.dry_run)
    todo = [b for b in blanks() if b[0] not in cache or distance_m(b[1], b[2], float(cache[b[0]]["lat"]), float(cache[b[0]]["lon"])) > 30]
    print(f"{len(todo)} non-home pins without an address are not cached yet ({len(cache)} cached)")
    if args.dry_run:
        return
    done = 0
    for vid, lat, lon, _region in todo[: args.limit]:
        try:
            res = lookup(lat, lon)
        except requests.RequestException as e:
            print("stopping on error:", e, file=sys.stderr)
            break
        addr = res.get("address", {}) or {}
        number, road = addr.get("house_number"), addr.get("road")
        city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("hamlet") or ""
        row = {"venue_id": vid, "lat": round(lat, 6), "lon": round(lon, 6), "status": "no_match", "address_line": "", "city": city, "distance_m": "",
               "osm_ref": f'{res.get("osm_type", "")}/{res.get("osm_id", "")}'.strip("/"), "queried_on": date.today().isoformat()}
        if number and road and "lat" in res:
            d = distance_m(lat, lon, float(res["lat"]), float(res["lon"]))
            row.update(status="address" if d <= MAX_DISTANCE_M else "too_far", distance_m=round(d))
            if row["status"] == "address":
                row["address_line"] = f"{number} {road}"
        elif road:
            row["status"] = "street_only"
            row["address_line"] = road
        cache[vid] = row
        done += 1
        save_cache(cache)   # after every pin: an interrupted run loses nothing
        time.sleep(1.1)     # policy: at most 1 request per second
    print(f"queried {done}")


if __name__ == "__main__":
    main()
