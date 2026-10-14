"""Extract hitting walls (handball courts, tennis backboards, practice walls) from OpenStreetMap (Overpass API).

    python ingestion/extract_osm_walls.py --area la          # quick, one metro
    python ingestion/extract_osm_walls.py --area metros      # LA, San Diego and the Bay Area (what the map currently has)
    python ingestion/extract_osm_walls.py --area california  # whole state, in tiles (slow on the free Overpass servers)

Output: data/raw/osm_walls.csv (one row per OSM element). Walls are separate from courts: see transform/models/core/dim_wall.sql.
"""
from __future__ import annotations

import argparse
import csv
import time
from datetime import datetime, timezone
from pathlib import Path

import overpass

# LA, San Diego, San Francisco, and the south and east Bay (San Jose to Oakland): the boxes the metro pass used
METROS = [overpass.BBOXES["la"], overpass.BBOXES["sd"], overpass.BBOXES["sf"], (37.2, -122.3, 37.6, -121.7), (37.6, -122.35, 38.0, -122.0)]

FIELDS = ["osm_type", "osm_id", "lat", "lon", "name", "sport", "surface", "lit", "access", "fee", "operator", "leisure",
          "tennis", "addr_city", "extracted_at", "region"]


def build_query(bbox) -> str:
    return f"""
    {overpass.header(bbox)}
    (
      nwr["leisure"="practice_wall"];
      nwr["tennis"="hitting_wall"];
      nwr["sport"~"(^|;)(american_handball|wallball)($|;)"];
      nwr["sport"~"(^|;)handball($|;)"]["name"~"wall|court|backboard",i];
      nwr["sport"~"(^|;)handball($|;)"]["sport"~"racquetball|squash|tennis|wallball"];
      nwr["sport"~"(^|;)(tennis|racquetball|squash|pickleball|paddle_tennis|paddleball)($|;)"]["name"~"practice wall|backboard|hitting wall",i];
    );
    out center tags;
    """


def to_row(el: dict, ts: str) -> dict:
    t = el.get("tags", {})
    c = el.get("center", {})
    return {
        "osm_type": el["type"], "osm_id": el["id"], "lat": el.get("lat", c.get("lat")), "lon": el.get("lon", c.get("lon")),
        "name": t.get("name"), "sport": t.get("sport"), "surface": t.get("surface"), "lit": t.get("lit"),
        "access": t.get("access"), "fee": t.get("fee"), "operator": t.get("operator"), "leisure": t.get("leisure"),
        "tennis": t.get("tennis"), "addr_city": t.get("addr:city"), "extracted_at": ts,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", choices=[*overpass.BBOXES, "metros", "california", "nevada"], default="la")
    ap.add_argument("--out", default="data/raw/osm_walls.csv")
    args = ap.parse_args()

    tiles = (METROS if args.area == "metros" else overpass.area_tiles(args.area))
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    seen: dict[tuple, dict] = {}
    failed: list = []
    for i, bbox in enumerate(tiles, 1):
        els = overpass.fetch_adaptive(build_query, bbox, f"tile {i}/{len(tiles)}", failed)
        for e in els:
            row = to_row(e, ts)
            if overpass.keep(row["lat"], row["lon"], "california" if args.area == "metros" else args.area):
                row["region"] = overpass.region_at(row["lat"], row["lon"])   # CA / NV from the border polygon (ADR 0014)
                seen[(e["type"], e["id"])] = row
        print(f"tile {i}/{len(tiles)} {bbox}: {len(els):>6,} elements (running unique: {len(seen):,})", flush=True)
        time.sleep(2)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(seen.values())
    print(f"Wrote {len(seen):,} rows to {out}")
    if failed:
        print(f"WARNING: {len(failed)} tile(s) failed and are MISSING from the output: {failed}")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
