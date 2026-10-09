"""Extract racket-sport courts from OpenStreetMap (Overpass API) for an area of California.

Usage:
    python ingestion/extract_osm_courts.py --area la          # Phase 1 default
    python ingestion/extract_osm_courts.py --area california  # whole state (slow; be kind to the free API)

Output: data/raw/osm_courts.csv  (one row per OSM element)
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

# south, west, north, east
BBOXES = {
    "la": (33.70, -118.67, 34.34, -118.15),
    "sf": (37.60, -122.55, 37.90, -122.30),
    "sd": (32.55, -117.30, 33.05, -116.95),
}

# OSM `sport=` values we care about. Keep in sync with transform/seeds/osm_sport_map.csv.
SPORT_KEYS = [
    "tennis", "pickleball", "padel", "squash", "badminton", "racquetball",
    "table_tennis", "paddle_tennis", "platform_tennis", "beach_tennis", "basque_pelota",
]

FIELDS = ["osm_type", "osm_id", "lat", "lon", "name", "sport", "surface", "lit",
          "access", "fee", "operator", "courts", "leisure", "extracted_at"]


def build_query(area: str) -> str:
    sports = "|".join(SPORT_KEYS)
    if area == "california":
        scope = 'area["ISO3166-2"="US-CA"]->.a;'
        filt = "(area.a)"
    else:
        s, w, n, e = BBOXES[area]
        scope = ""
        filt = f"({s},{w},{n},{e})"
    return f"""
    [out:json][timeout:300];
    {scope}
    (
      nwr["sport"~"^({sports})($|;)|;({sports})($|;)"]["leisure"~"pitch|sports_centre|fitness_centre"]{filt};
    );
    out center tags;
    """


def fetch(query: str) -> list[dict]:
    last_err: Exception | None = None
    for url in OVERPASS_URLS:
        for attempt in range(3):
            try:
                r = requests.post(url, data={"data": query}, timeout=330,
                                  headers={"User-Agent": "courtconnect-ca/0.1 (portfolio project)"})
                r.raise_for_status()
                return r.json()["elements"]
            except Exception as err:  # noqa: BLE001 - retry on any transport/parse error
                last_err = err
                wait = 5 * (attempt + 1)
                print(f"  {url} attempt {attempt + 1} failed ({err}); retrying in {wait}s", file=sys.stderr)
                time.sleep(wait)
    raise RuntimeError(f"All Overpass endpoints failed: {last_err}")


def to_row(el: dict, ts: str) -> dict:
    tags = el.get("tags", {})
    # ways/relations carry a computed centre; nodes carry lat/lon directly
    center = el.get("center", {})
    return {
        "osm_type": el["type"],
        "osm_id": el["id"],
        "lat": el.get("lat", center.get("lat")),
        "lon": el.get("lon", center.get("lon")),
        "name": tags.get("name"),
        "sport": tags.get("sport"),
        "surface": tags.get("surface"),
        "lit": tags.get("lit"),
        "access": tags.get("access"),
        "fee": tags.get("fee"),
        "operator": tags.get("operator"),
        "courts": tags.get("courts"),
        "leisure": tags.get("leisure"),
        "extracted_at": ts,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", choices=[*BBOXES, "california"], default="la")
    ap.add_argument("--out", default="data/raw/osm_courts.csv")
    args = ap.parse_args()

    print(f"Querying Overpass for area={args.area} ...")
    elements = fetch(build_query(args.area))
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = [to_row(e, ts) for e in elements]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows):,} rows to {out}")


if __name__ == "__main__":
    main()
