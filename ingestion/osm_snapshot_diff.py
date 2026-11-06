"""Diff two OSM court extracts for the racket sports: new, gone (deleted or retagged), moved, renamed, sport_changed.

The OSM side of the closure signal that overture_release_diff.py gives Overture (ADR 0026, option A: snapshot diff).
Writes a CSV only; nothing public.

    python ingestion/osm_snapshot_diff.py                 # saved manifest vs the extract now in the raw folder, then rotate the manifest
    python ingestion/osm_snapshot_diff.py --no-verify     # offline: skip the Overpass check of the gone ids
    python ingestion/osm_snapshot_diff.py --dry-run       # print what it would do; write and rotate nothing
    python ingestion/osm_snapshot_diff.py --old-dir DIR --new-dir DIR --out-dir DIR --seed FILE   # fixtures / tests

Why a manifest: `make extract` overwrites data/raw/osm_courts*.csv, so after it only the newest extract exists. Run this AFTER
each OSM extract (any order relative to `make load`): it diffs the manifest saved by the previous run against the extract now
on disk, then replaces the manifest with the new extract's ids. The manifest is data/raw/osm_snapshot/<same file name> with only
the columns a diff needs (osm_type, osm_id, lat, lon, name, sport, leisure, region, extracted_at; ~2 MB for California), kept in
the shared raw folder and not committed (about 2 MB of git history twice a month). The first run has nothing to compare with:
it saves the manifest and says so. A region file is only diffed when its newest `extracted_at` changed, so a one-state re-extract
leaves the other states' manifests alone.

An element missing from the new extract was deleted, lost its racket sport/leisure tags, or was dropped by a flaky Overpass tile.
Unless --no-verify, the gone ids are looked up in Overpass (one small query per 400 ids): still tagged for a racket court ->
extract miss, ignored; absent -> `deleted`; present without the tags -> `retagged`. Without the lookup the kind is `gone`.

Output: data/raw/osm_snapshot_diff.csv. Gone rows are also added to transform/seeds/osm_gone_elements.csv (the manifest and the raw
extract are overwritten, so the seed is the only lasting memory): a closure signal, not a closure (mart_venue_closure_signal).
A file whose extract shrank by more than 10% (a failed tile?) is refused unless --force, and its manifest is kept.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import Counter
from pathlib import Path

from extract_osm_courts import LEISURE, SPORT_KEYS
from rawdir import raw_dir

MANIFEST_FIELDS = ["osm_type", "osm_id", "lat", "lon", "name", "sport", "leisure", "region", "extracted_at"]
OUT_FIELDS = ["kind", "osm_type", "osm_id", "name", "sport", "leisure", "region", "lat", "lon", "old_extract", "new_extract", "detail"]
GONE_FIELDS = ["element_id", "osm_name", "sport", "leisure", "lat", "lon", "region", "last_seen_extract", "gone_in_extract", "kind"]
GONE_SEED = Path(__file__).resolve().parent.parent / "transform" / "seeds" / "osm_gone_elements.csv"
MOVED_M = 25            # a court node nudged a few metres is a mapper's tidy-up; 25 m+ is a different spot
MAX_SHRINK = 0.10       # same guard as load_raw.py
VERIFY_CHUNK = 400


def raw_files(folder: Path) -> list[Path]:
    """osm_courts.csv (California) plus one osm_courts_<code>.csv per other region, the same set load_raw.py reads."""
    return [p for p in [folder / "osm_courts.csv", *sorted(folder.glob("osm_courts_??.csv"))] if p.exists()]


def read_manifest(path: Path) -> dict[tuple[str, str], dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return {(r["osm_type"], r["osm_id"]): {k: r.get(k) or "" for k in MANIFEST_FIELDS} for r in csv.DictReader(f)}


def extract_date(rows: dict) -> str:
    """The extract's own timestamp (newest `extracted_at`), '' for an empty file."""
    return max((r["extracted_at"] for r in rows.values()), default="")


def metres(a: dict, b: dict) -> float:
    la1, lo1, la2, lo2 = (float(x) for x in (a["lat"], a["lon"], b["lat"], b["lon"]))
    return math.hypot((lo2 - lo1) * 111_320 * math.cos(math.radians((la1 + la2) / 2)), (la2 - la1) * 111_320)


def sport_set(value: str) -> frozenset[str]:
    return frozenset(s for s in value.lower().replace(" ", "").split(";") if s)


def diff(old: dict, new: dict, old_ext: str, new_ext: str) -> list[dict]:
    out = []

    def add(kind: str, row: dict, detail: str = "") -> None:
        out.append({"kind": kind, "osm_type": row["osm_type"], "osm_id": row["osm_id"], "name": row["name"], "sport": row["sport"],
                    "leisure": row["leisure"], "region": row["region"], "lat": row["lat"], "lon": row["lon"],
                    "old_extract": old_ext, "new_extract": new_ext, "detail": detail})

    for key, n in new.items():
        o = old.get(key)
        if o is None:
            add("new", n, f"sport={n['sport']}")
            continue
        if sport_set(o["sport"]) != sport_set(n["sport"]):
            add("sport_changed", n, f"{o['sport']} -> {n['sport']}")
        if o["name"].strip().lower() != n["name"].strip().lower():
            add("renamed", n, f"{o['name'] or '(unnamed)'} -> {n['name'] or '(unnamed)'}")
        if o["lat"] and n["lat"] and (d := metres(o, n)) > MOVED_M:
            add("moved", n, f"{d:.0f} m")
    for key, o in old.items():
        if key not in new:
            add("gone", o, "not in the new extract (deleted, lost its racket tags, or an Overpass tile dropped it)")
    return out


def is_racket_court(tags: dict) -> bool:
    """Would extract_osm_courts.py's query still return an element with these tags?"""
    sports = {s.strip() for s in (tags.get("sport") or "").split(";")}
    return bool(sports & set(SPORT_KEYS)) and (tags.get("leisure") in LEISURE.split("|") or tags.get("club") == "sport")


def classify_gone(current: dict | None) -> str:
    """`current` = the element's tags in OSM today (None = no such element). Returns deleted | retagged | still_listed."""
    if current is None:
        return "deleted"
    return "still_listed" if is_racket_court(current) else "retagged"


def fetch_current(keys: list[tuple[str, str]]) -> dict[tuple[str, str], dict]:
    """Tags of the elements that still exist, from Overpass (ids only, so a few hundred per query)."""
    import overpass
    found: dict[tuple[str, str], dict] = {}
    for i in range(0, len(keys), VERIFY_CHUNK):
        part = keys[i:i + VERIFY_CHUNK]
        by_type = {t: [oid for ty, oid in part if ty == t] for t in ("node", "way", "relation")}
        body = "".join(f"{t}(id:{','.join(ids)});" for t, ids in by_type.items() if ids)
        for e in overpass.run(f"[out:json][timeout:120];({body});out tags;", f"verify {i // VERIFY_CHUNK + 1}"):
            found[(e["type"], str(e["id"]))] = e.get("tags", {})
    return found


def verify(rows: list[dict]) -> tuple[list[dict], int]:
    """Replace `gone` with deleted/retagged using Overpass; drop extract misses. Returns (rows, misses)."""
    gone = [r for r in rows if r["kind"] == "gone"]
    if not gone:
        return rows, 0
    try:
        current = fetch_current([(r["osm_type"], r["osm_id"]) for r in gone])
    except Exception as err:  # noqa: BLE001 - keep the unverified kind rather than lose the diff
        print(f"  WARNING: could not verify {len(gone)} gone ids ({err}); kept as `gone`")
        return rows, 0
    out, misses = [], 0
    for r in rows:
        if r["kind"] != "gone":
            out.append(r)
            continue
        kind = classify_gone(current.get((r["osm_type"], r["osm_id"])))
        if kind == "still_listed":
            misses += 1
            continue
        out.append({**r, "kind": kind, "detail": "no such element in OSM any more" if kind == "deleted" else "still in OSM, but no longer tagged as a racket court"})
    return out, misses


def update_gone_seed(rows: list[dict], path: Path = GONE_SEED) -> int:
    """Add the gone rows to the seed, one row per element. A first sighting stays; an element that came back and vanished again
    takes the newer dates. Returns how many rows were added or refreshed."""
    have: dict[str, dict] = {}
    if path.exists():
        with path.open(encoding="utf-8", newline="") as f:
            have = {r["element_id"]: r for r in csv.DictReader(f)}
    changed = 0
    for r in rows:
        if r["kind"] not in ("gone", "deleted", "retagged"):
            continue
        eid = f"{r['osm_type']}/{r['osm_id']}"
        row = {"element_id": eid, "osm_name": r["name"].strip(), "sport": r["sport"], "leisure": r["leisure"], "lat": r["lat"], "lon": r["lon"],
               "region": r["region"], "last_seen_extract": r["old_extract"][:10], "gone_in_extract": r["new_extract"][:10], "kind": r["kind"]}
        if eid not in have or have[eid]["gone_in_extract"] < row["gone_in_extract"]:
            have[eid] = row
            changed += 1
    if changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=GONE_FIELDS, lineterminator="\n")
            w.writeheader()
            w.writerows(have.values())
    return changed


def save_manifest(rows: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows.values())


def run_file(raw: Path, manifest_dir: Path, args) -> list[dict]:
    new = read_manifest(raw)
    manifest = manifest_dir / raw.name
    new_ext = extract_date(new)
    if not manifest.exists():
        if not args.dry_run:
            save_manifest(new, manifest)
        print(f"{raw.name}: no earlier snapshot; {'would save' if args.dry_run else 'saved'} {len(new):,} ids as the baseline (the first diff comes after the next extract)")
        return []
    old = read_manifest(manifest)
    old_ext = extract_date(old)
    if new_ext == old_ext:
        print(f"{raw.name}: same extract as the saved snapshot ({new_ext[:10]}); nothing to diff")
        return []
    if new_ext < old_ext:
        print(f"{raw.name}: extract {new_ext[:10]} is OLDER than the snapshot {old_ext[:10]}; skipped")
        return []
    rows = diff(old, new, old_ext, new_ext)
    gone = sum(r["kind"] == "gone" for r in rows)
    if old and gone > MAX_SHRINK * len(old) and not args.force:
        print(f"{raw.name}: {gone:,} of {len(old):,} elements gone (> {MAX_SHRINK:.0%}); looks like a partial extract. Skipped, snapshot kept; --force to accept")
        return []
    misses = 0
    if not args.no_verify:
        rows, misses = verify(rows)
    print(f"{raw.name}: OSM {old_ext[:10]} ({len(old):,}) -> {new_ext[:10]} ({len(new):,}): "
          + (", ".join(f"{k} {n}" for k, n in sorted(Counter(r['kind'] for r in rows).items())) or "no changes")
          + (f"; {misses} ids still tagged in OSM (extract misses, ignored)" if misses else ""))
    if not args.dry_run:
        save_manifest(new, manifest)
    return rows


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--new-dir", default=raw_dir(), type=Path, help="folder holding the current osm_courts*.csv")
    ap.add_argument("--old-dir", default=None, type=Path, help="manifest folder (default: <new-dir>/osm_snapshot)")
    ap.add_argument("--out-dir", default=None, type=Path, help="where osm_snapshot_diff.csv goes (default: <new-dir>)")
    ap.add_argument("--seed", default=GONE_SEED, type=Path)
    ap.add_argument("--no-verify", action="store_true", help="skip the Overpass lookup of the gone ids")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="accept an extract that shrank by more than 10%%")
    args = ap.parse_args()
    manifest_dir = args.old_dir or args.new_dir / "osm_snapshot"

    files = raw_files(args.new_dir)
    if not files:
        raise SystemExit(f"no osm_courts*.csv in {args.new_dir}; run the extract first")
    rows = [r for f in files for r in run_file(f, manifest_dir, args)]
    if args.dry_run:
        print("Dry run: nothing written.")
        return
    out = (args.out_dir or args.new_dir) / "osm_snapshot_diff.csv"
    if rows:
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=OUT_FIELDS)
            w.writeheader()
            w.writerows(rows)
        print(f"Wrote {len(rows):,} changes to {out}")
    print(f"Added {update_gone_seed(rows, args.seed)} gone elements to {args.seed}")


if __name__ == "__main__":
    main()
