"""Diff two Overture places releases for CA+NV racket places: new, gone, closed, reopened, renamed, moved.

Feeds the change feed planned in ADR 0025 (`app/data/changes.json`); it writes a CSV only, nothing public yet.

    python ingestion/overture_release_diff.py                      # old = the shared raw snapshot, new = newest release
    python ingestion/overture_release_diff.py --new-release 2026-10-21.0
    python ingestion/overture_release_diff.py --old path/to/overture_places.csv

The old side is read from a local extract (its `release` column says which release it is), the new side is read from S3
with the same query as extract_overture_places.py. The shared raw CSV is NOT overwritten: run the extract for that.
Overture ids (GERS) are stable across releases, so places are matched by id.

Output: data/raw/overture_release_diff.csv
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import Counter
from pathlib import Path

from extract_overture_places import FIELDS, fetch_places, latest_release, norm
from rawdir import raw_path

CLOSED = {"permanently_closed", "temporarily_closed"}
MOVED_M = 100
OUT_FIELDS = ["kind", "place_id", "name", "category", "city", "lat", "lon", "old_release", "new_release", "detail", "already_in_closed_places"]


def metres(a: dict, b: dict) -> float:
    la1, lo1, la2, lo2 = (float(x) for x in (a["lat"], a["lon"], b["lat"], b["lon"]))
    dy = (la2 - la1) * 111_320
    dx = (lo2 - lo1) * 111_320 * math.cos(math.radians((la1 + la2) / 2))
    return math.hypot(dx, dy)


def diff(old: dict[str, dict], new: dict[str, dict], old_rel: str, new_rel: str, known_closed: set[str]) -> list[dict]:
    out = []

    def add(kind: str, row: dict, detail: str = "") -> None:
        out.append({"kind": kind, "place_id": row["place_id"], "name": row["name"], "category": row["category"],
                    "city": row["city"], "lat": row["lat"], "lon": row["lon"], "old_release": old_rel,
                    "new_release": new_rel, "detail": detail,
                    "already_in_closed_places": "yes" if row["place_id"] in known_closed else ""})

    for pid, n in new.items():
        o = old.get(pid)
        if o is None:
            add("new", n, n["category"])
            continue
        if n["operating_status"] in CLOSED and o["operating_status"] not in CLOSED:
            add("closed", n, f"{o['operating_status'] or 'unset'} -> {n['operating_status']}")
        elif o["operating_status"] in CLOSED and n["operating_status"] not in CLOSED:
            add("reopened", n, f"{o['operating_status']} -> {n['operating_status'] or 'unset'}")
        if norm(o["name"]) != norm(n["name"]):
            add("renamed", n, f"{o['name']} -> {n['name']}")
        d = metres(o, n)
        if d > MOVED_M:
            add("moved", n, f"{d:.0f} m")
    for pid, o in old.items():
        if pid not in new:
            add("gone", o, "not in the new release (or no longer matches the racket filter)")
    return out


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", default=raw_path("overture_places.csv"))
    ap.add_argument("--new-release", default=None)
    ap.add_argument("--out", default=raw_path("overture_release_diff.csv"))
    args = ap.parse_args()

    old_rows = list(csv.DictReader(Path(args.old).open(encoding="utf-8")))
    old_rel = Counter(r["release"] for r in old_rows).most_common(1)[0][0]
    new_rel = args.new_release or latest_release()
    if old_rel == new_rel:
        raise SystemExit(f"old and new are both release {new_rel}; nothing to diff")
    print(f"Overture {old_rel} ({len(old_rows):,} places, local) -> {new_rel} (reading S3)")

    new_rows = [dict(zip(FIELDS, r)) for r in fetch_places(new_rel)]
    for r in new_rows:
        for k in ("operating_status", "city"):
            r[k] = r[k] or ""
    closed_seed = Path("transform/seeds/closed_places.csv")
    known_closed = {r["place_id"] for r in csv.DictReader(closed_seed.open(encoding="utf-8"))} if closed_seed.exists() else set()

    rows = diff({r["place_id"]: r for r in old_rows}, {r["place_id"]: r for r in new_rows}, old_rel, new_rel, known_closed)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=OUT_FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows):,} changes to {out}: " + ", ".join(f"{k} {n}" for k, n in sorted(Counter(r["kind"] for r in rows).items())))


if __name__ == "__main__":
    main()
