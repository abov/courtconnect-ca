"""Extract racket-sport courts and facilities from OpenStreetMap (Overpass API).

    python ingestion/extract_osm_courts.py --area la          # quick, one metro
    python ingestion/extract_osm_courts.py --area california  # whole state, in tiles (several minutes)

Output: data/raw/osm_courts.csv  (one row per OSM element, de-duplicated across tiles)
"""
from __future__ import annotations

import argparse
import csv
import time
from datetime import datetime, timezone
from pathlib import Path

import overpass

# OSM `sport=` values we search for. Keep in sync with transform/seeds/osm_sport_map.csv.
SPORT_KEYS = [
    "tennis", "table_tennis", "tennis_table", "pickleball", "padel", "padel_tennis", "badminton", "squash",
    "racquetball", "outdoor_racquetball", "paddle_tennis", "platform_tennis", "beach_tennis", "beachtennis",
    "pelota", "fronton", "basque_pelota", "frontenis", "paddleball",
    "tamburello", "real_tennis", "jai_alai", "jeu_de_paume", "soft_tennis", "touchtennis", "swingball",
]

# leisure types that are a court ('pitch') or a facility that contains/names courts
LEISURE = "pitch|sports_centre|sports_hall|fitness_centre|stadium"

FIELDS = ["osm_type", "osm_id", "lat", "lon", "name", "sport", "surface", "lit", "access", "fee", "operator",
          "courts", "leisure", "indoor", "covered", "building", "website", "phone", "opening_hours",
          "addr_housenumber", "addr_street", "addr_city", "extracted_at"]


def build_query(bbox) -> str:
    sports = "|".join(SPORT_KEYS)
    sport_re = f"(^|;)({sports})($|;)"
    return f"""
    {overpass.header(bbox)}
    (
      nwr["sport"~"{sport_re}"]["leisure"~"^({LEISURE})$"];
      nwr["sport"~"{sport_re}"]["club"="sport"];
    );
    out center tags;
    """


def to_row(el: dict, ts: str) -> dict:
    t = el.get("tags", {})
    c = el.get("center", {})
    return {
        "osm_type": el["type"], "osm_id": el["id"],
        "lat": el.get("lat", c.get("lat")), "lon": el.get("lon", c.get("lon")),
        "name": t.get("name"), "sport": t.get("sport"), "surface": t.get("surface"), "lit": t.get("lit"),
        "access": t.get("access"), "fee": t.get("fee"), "operator": t.get("operator"), "courts": t.get("courts"),
        "leisure": t.get("leisure") or ("club" if t.get("club") else None),
        "indoor": t.get("indoor"), "covered": t.get("covered"), "building": t.get("building"),
        "website": t.get("website") or t.get("contact:website"),
        "phone": t.get("phone") or t.get("contact:phone"),
        "opening_hours": t.get("opening_hours"),
        "addr_housenumber": t.get("addr:housenumber"), "addr_street": t.get("addr:street"),
        "addr_city": t.get("addr:city"), "extracted_at": ts,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", choices=[*overpass.BBOXES, "california"], default="la")
    ap.add_argument("--out", default="data/raw/osm_courts.csv")
    args = ap.parse_args()

    tiles = overpass.california_tiles() if args.area == "california" else [overpass.BBOXES[args.area]]
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    seen: dict[tuple, dict] = {}
    failed: list = []
    for i, bbox in enumerate(tiles, 1):
        els = overpass.fetch_adaptive(build_query, bbox, f"tile {i}/{len(tiles)}", failed)
        for e in els:
            row = to_row(e, ts)
            if overpass.in_california(row["lat"], row["lon"]):   # drop Nevada / Oregon / Mexico / ocean
                seen[(e["type"], e["id"])] = row
        print(f"tile {i}/{len(tiles)} {bbox}: {len(els):>6,} elements (running unique: {len(seen):,})", flush=True)
        time.sleep(2)  # be polite to the free public API

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
