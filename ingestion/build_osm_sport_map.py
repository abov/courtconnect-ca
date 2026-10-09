"""Build transform/seeds/osm_sport_map.csv: which OSM `sport=` value means which sport on the master sheet.

Sport names are resolved against the synced sheet (all_racquet.csv) by prefix, so a typo here fails loudly
instead of silently dropping a sport. `confidence` says how safe the mapping is:
  high   - OSM value and sheet sport are the same thing
  medium - OSM value is ambiguous or regional; verify before relying on it

OSM tag vocabulary checked against taginfo.openstreetmap.org (sport=*), Oct 2026.
Sports with NO OSM tag at all (Jokari, Tamburello, Toccer, ...) are reported by mart_sport_gaps.

    python ingestion/build_osm_sport_map.py
"""
from __future__ import annotations

import csv
from pathlib import Path

SEEDS = Path("transform/seeds")

# osm sport value -> (sheet sport name prefix, confidence)
MAP = [
    ("tennis", "Tennis", "high"),
    ("table_tennis", "Table Tennis", "high"),
    ("tennis_table", "Table Tennis", "high"),
    ("pickleball", "Pickleball", "high"),
    ("padel", "Padel", "high"),
    ("padel_tennis", "Padel", "high"),
    ("badminton", "Badminton", "high"),
    ("squash", "Squash", "high"),
    ("racquetball", "Racquetball", "high"),
    ("outdoor_racquetball", "Outdoor Racquetball", "high"),
    ("paddle_tennis", "Pop Tennis", "medium"),
    ("platform_tennis", "Platform Tennis", "high"),
    ("beach_tennis", "Beach Tennis", "high"),
    ("beachtennis", "Beach Tennis", "high"),
    ("pelota", "Paleta front", "medium"),
    ("fronton", "Paleta front", "medium"),
    ("basque_pelota", "Basque Pelota", "medium"),
    ("frontenis", "Frontenis", "high"),
    ("paddleball", "4-wall Paddle", "medium"),
    ("tamburello", "Tamburello", "high"),
    ("real_tennis", "Real Tennis", "high"),
    ("jai_alai", "Jai alai", "high"),
    ("jeu_de_paume", "Hand Tennis", "medium"),
    ("soft_tennis", "Soft Tennis", "high"),
    ("swingball", "Totem Tennis", "medium"),
    ("touchtennis", "Touchtennis", "high"),
]


def main() -> None:
    with (SEEDS / "all_racquet.csv").open(encoding="utf-8", newline="") as f:
        sports = [r["sport"].strip() for r in csv.DictReader(f)]

    rows = []
    for key, prefix, conf in MAP:
        exact = [s for s in sports if s.lower() == prefix.lower()]
        hits = exact or [s for s in sports if s.lower().startswith(prefix.lower())]
        if len(hits) != 1:
            raise SystemExit(f"OSM value {key!r}: prefix {prefix!r} matched {len(hits)} sports {hits}")
        rows.append({"osm_sport_key": key, "sport": hits[0], "confidence": conf})

    out = SEEDS / "osm_sport_map.csv"
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["osm_sport_key", "sport", "confidence"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    covered = len({r["sport"] for r in rows})
    print(f"Wrote {len(rows)} mappings covering {covered} of {len(sports)} sheet sports -> {out}")


if __name__ == "__main__":
    main()
