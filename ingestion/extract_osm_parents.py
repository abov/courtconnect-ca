"""Extract NAMED parent features (parks, schools, clubs, sports centres...) with bounding boxes.

Courts are usually unnamed; the park, school or club they sit inside usually has a name. dbt joins each court
to the smallest named feature whose bounding box contains it (see int_court_parent).

    python ingestion/extract_osm_parents.py --area california
Output: data/raw/osm_parents.csv
"""
from __future__ import annotations

import argparse
import csv
import time
from datetime import datetime, timezone
from pathlib import Path

import overpass

# (osm key, value regex)
KINDS = [
    ("leisure", "park|recreation_ground|sports_centre|stadium|fitness_centre|golf_course|garden"),
    ("amenity", "school|college|university|community_centre|clubhouse"),
    ("club", "sport"),
    ("tourism", "resort|hotel|camp_site"),
]
FIELDS = ["osm_type", "osm_id", "name", "kind", "minlat", "minlon", "maxlat", "maxlon", "extracted_at"]


def build_query(bbox) -> str:
    clauses = "\n".join(f'      wr["{k}"~"^({v})$"]["name"];' for k, v in KINDS)
    return f"""
    {overpass.header(bbox)}
    (
{clauses}
    );
    out tags bb;
    """


def kind_of(tags: dict) -> str:
    for k, _ in KINDS:
        if tags.get(k):
            return f"{k}={tags[k]}"
    return "other"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", choices=[*overpass.BBOXES, "california"], default="la")
    ap.add_argument("--out", default="data/raw/osm_parents.csv")
    args = ap.parse_args()

    tiles = overpass.california_tiles() if args.area == "california" else [overpass.BBOXES[args.area]]
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    seen: dict[tuple, dict] = {}
    failed: list = []
    for i, bbox in enumerate(tiles, 1):
        els = overpass.fetch_adaptive(build_query, bbox, f"tile {i}/{len(tiles)}", failed)
        for e in els:
            b = e.get("bounds")
            if not b or not overpass.in_california((b["minlat"] + b["maxlat"]) / 2, (b["minlon"] + b["maxlon"]) / 2):
                continue
            seen[(e["type"], e["id"])] = {
                "osm_type": e["type"], "osm_id": e["id"], "name": e["tags"]["name"], "kind": kind_of(e["tags"]),
                "minlat": b["minlat"], "minlon": b["minlon"], "maxlat": b["maxlat"], "maxlon": b["maxlon"],
                "extracted_at": ts,
            }
        print(f"tile {i}/{len(tiles)} {bbox}: {len(els):>6,} features (running unique: {len(seen):,})", flush=True)
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
