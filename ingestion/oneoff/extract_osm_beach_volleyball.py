"""Find beach / sand volleyball courts in CA + NV from OpenStreetMap (Overpass API).

Why: sand courts can be reused for Pro Sunball (sheet sport; no court data of its own).
These rows are CANDIDATES (inferred from the volleyball tag), not confirmed Pro Sunball venues.

    python ingestion/oneoff/extract_osm_beach_volleyball.py            # both states, ~ a few minutes

Output: data/raw/osm_beach_volleyball.csv (one row per OSM element, de-duplicated across tiles)
Not loaded into dbt: a scan to size the opportunity first.
"""
from __future__ import annotations

import csv
import time
from datetime import datetime, timezone
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # shared helpers in ingestion/
import overpass
from rawdir import raw_path

FIELDS = ["osm_type", "osm_id", "lat", "lon", "name", "sport", "surface", "leisure", "access", "fee", "operator",
          "courts", "lit", "indoor", "website", "addr_street", "addr_city", "match", "extracted_at", "region"]


def build_query(bbox) -> str:
    return f"""
    {overpass.header(bbox)}
    (
      nwr["sport"~"(^|;)(beachvolleyball|beach_volleyball)($|;)"];
      nwr["sport"="volleyball"]["surface"~"^(sand|beach)$"];
      nwr["sport"="volleyball"]["leisure"="beach_resort"];
    );
    out center tags;
    """


def to_row(el: dict, ts: str) -> dict:
    t = el.get("tags", {})
    c = el.get("center", {})
    sport = t.get("sport") or ""
    return {
        "osm_type": el["type"], "osm_id": el["id"],
        "lat": el.get("lat", c.get("lat")), "lon": el.get("lon", c.get("lon")),
        "name": t.get("name"), "sport": sport, "surface": t.get("surface"), "leisure": t.get("leisure"),
        "access": t.get("access"), "fee": t.get("fee"), "operator": t.get("operator"), "courts": t.get("courts"),
        "lit": t.get("lit"), "indoor": t.get("indoor"), "website": t.get("website") or t.get("contact:website"),
        "addr_street": t.get("addr:street"), "addr_city": t.get("addr:city"),
        "match": "tagged_beachvolleyball" if "beach" in sport else "volleyball_on_sand",
        "extracted_at": ts,
    }


def main() -> None:
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    seen: dict[tuple, dict] = {}
    failed: list = []
    for area in ("california", "nevada"):
        tiles = overpass.area_tiles(area)
        for i, bbox in enumerate(tiles, 1):
            els = overpass.fetch_adaptive(build_query, bbox, f"{area} {i}/{len(tiles)}", failed)
            for e in els:
                row = to_row(e, ts)
                if row["lat"] is None or not overpass.keep(row["lat"], row["lon"], area):
                    continue
                row["region"] = overpass.region_at(row["lat"], row["lon"])
                seen[(e["type"], e["id"])] = row
            print(f"{area} {i}/{len(tiles)}: {len(els):>5} elements (unique so far {len(seen):,})", flush=True)
            time.sleep(2)

    out = Path(raw_path("osm_beach_volleyball.csv"))
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(seen.values())
    print(f"Wrote {len(seen):,} rows to {out}")
    if failed:
        print(f"WARNING: {len(failed)} tile(s) failed and are MISSING: {failed}")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
