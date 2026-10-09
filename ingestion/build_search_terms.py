"""Build transform/seeds/sport_search_terms.csv: business-name words that suggest a place offers a sport.

Terms come from the master sheet (sport names with parentheticals stripped, split on '/' and ','), plus the alias seed.
Each term gets a reliability:
  distinctive - a name containing it almost certainly offers the sport ("padel", "pickleball", "squash" ...)
  ambiguous   - a name containing it MAY mean something else ("Real Tennis" matches "Camino Real Tennis Center",
                "Beach Tennis" matches "Pacific Beach Tennis Club", "Ricochet" matches a horse ranch). Matches
                on these are kept as weak evidence and never counted as a confirmed venue for the sport.

Edit DISTINCTIVE below (or add aliases to sport_aliases.csv) and re-run:   python ingestion/build_search_terms.py
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

SEEDS = Path("transform/seeds")

# Terms trusted on their own. Everything else is 'ambiguous'.
DISTINCTIVE = {
    "tennis", "pickleball", "padel", "squash", "racquetball", "badminton", "table tennis", "ping pong",
    "platform tennis", "paddle tennis", "pop tennis", "frescobol", "tamburello", "jai alai", "soft tennis",
    "jokari", "smolball", "speedminton", "crossminton", "matkot", "racquet club", "racket club", "pickle ball",
    "paddleball", "touchtennis",
}

# Extra spellings people use in business names; (term, sport on the sheet)
EXTRA = [("pickle ball", "Pickleball"), ("racquet club", "Tennis"), ("racket club", "Tennis"),
         ("ping pong", "Table Tennis"), ("paddleball", "4-wall Paddle")]


def main() -> None:
    with (SEEDS / "all_racquet.csv").open(encoding="utf-8", newline="") as f:
        sheet = [r["sport"].strip() for r in csv.DictReader(f)]
    terms: dict[str, str] = {}
    for sport in sheet:
        base = re.sub(r"\s*\(.*?\)", "", sport)
        for piece in re.split(r"[/,]", base):
            t = re.sub(r"[^a-z0-9 ]+", " ", piece.lower()).strip()
            t = re.sub(r"\s+", " ", t)
            if len(t) >= 4:
                terms.setdefault(t, sport)
    with (SEEDS / "sport_aliases.csv").open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            t = re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", r["alias"].lower())).strip()
            if len(t) >= 4 and r["sport"] in sheet:
                terms.setdefault(t, r["sport"])
    for t, s in EXTRA:
        if s in sheet:
            terms.setdefault(t, s)

    out = SEEDS / "sport_search_terms.csv"
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["term", "sport", "reliability"])
        for t, s in sorted(terms.items()):
            w.writerow([t, s, "distinctive" if t in DISTINCTIVE else "ambiguous"])
    d = sum(1 for t in terms if t in DISTINCTIVE)
    print(f"Wrote {len(terms)} search terms ({d} distinctive, {len(terms) - d} ambiguous) -> {out}")


if __name__ == "__main__":
    main()
