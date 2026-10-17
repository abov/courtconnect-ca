"""Tier 3 of address fill (docs/ml_plan.md): reverse-geocode pins that still have no street address, via OSM's Nominatim.

Only NON-HOME pins with no address after tiers 1-2 (`int_venue_address`) are queried; home-like pins stay city-only (owner rule).
Results are cached in transform/seeds/nominatim_addresses.csv, one row per pin including misses, so a rerun never re-queries.

Nominatim usage policy (operations.osmfoundation.org/policies/nominatim): one request a second, a single thread, an identifying
User-Agent, results stored, no grid sweeps. This sends pin coordinates only (no email or other personal contact).

    python ingestion/reverse_geocode_blanks.py --limit 25     # query up to 25 uncached pins (sample); omit --limit for all
    python ingestion/reverse_geocode_blanks.py --dry-run      # count what would be queried
    python ingestion/reverse_geocode_blanks.py --city-only    # pins still without a city (home-like ones too): city-level lookup, no street kept

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
UA = {"User-Agent": "courtconnect-ca/0.1 (+https://github.com/abov/courtconnect-ca)"}
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


def city_blanks() -> list[tuple]:
    """Pins that still have no city after the Overture city search. A city never names a street, so home-like pins are included."""
    con = duckdb.connect(str(ROOT / "courtconnect.duckdb"), read_only=True)
    return con.execute("""
        select a.venue_id, v.lat, v.lon, v.region
        from intermediate.int_venue_address a join core.dim_venue v using (venue_id)
        where (a.city is null or a.city = '') and v.lat is not null and v.lon is not null
        order by hash(a.venue_id)
    """).fetchall()


def lookup(lat: float, lon: float, zoom: int = 18) -> dict:
    r = requests.get(URL, headers=UA, timeout=30,
                     params={"lat": lat, "lon": lon, "format": "jsonv2", "zoom": zoom, "addressdetails": 1})
    r.raise_for_status()
    return r.json()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--city-only", action="store_true", help="fill missing cities at city zoom; never stores a street for these pins")
    args = ap.parse_args()
    cache = load_cache()
    if args.city_only:
        run_city_only(cache, args)
        return
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


def run_city_only(cache: dict[str, dict], args) -> None:
    """City-level lookup (zoom 10) for pins with no city. A pin already cached keeps its row and gains the city; a new pin is cached as
    status city_only with no address_line, so a home-like pin never gets a street. Same rate limit and User-Agent as the street lookup."""
    todo = []
    for vid, lat, lon, _region in city_blanks():
        row = cache.get(vid)
        if row and distance_m(lat, lon, float(row["lat"]), float(row["lon"])) <= 30 and row["status"] == "city_only":
            continue   # already tried at city level; a miss is cached too
        todo.append((vid, lat, lon))
    print(f"{len(todo)} pins without a city to look up ({len(cache)} cached)")
    if args.dry_run:
        return
    done = 0
    for vid, lat, lon in todo[: args.limit]:
        try:
            res = lookup(lat, lon, zoom=10)
        except requests.RequestException as e:
            print("stopping on error:", e, file=sys.stderr)
            break
        addr = res.get("address", {}) or {}
        city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("hamlet") or ""
        row = cache.get(vid)
        if row and distance_m(lat, lon, float(row["lat"]), float(row["lon"])) <= 30:
            row["city"] = city or row["city"]      # keep the street lookup (status, address_line) as it was
        else:
            cache[vid] = {"venue_id": vid, "lat": round(lat, 6), "lon": round(lon, 6), "status": "city_only", "address_line": "", "city": city,
                          "distance_m": "", "osm_ref": "", "queried_on": date.today().isoformat()}
        done += 1
        save_cache(cache)
        time.sleep(1.1)
    print(f"queried {done}")


if __name__ == "__main__":
    main()
