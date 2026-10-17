"""Score the Overture place -> OSM facility match against hand-checked pairs.

    python ingestion/eval_match_gold.py            (or: make eval-match)    needs the local DuckDB built by dbt
    python ingestion/eval_match_gold.py --check    validates the gold file only (no database; this is what CI runs)

Gold file: ci/gold/place_osm_pairs.csv (plan: docs/gold_set_plan.md). One row per pair:
  place_id     Overture place id
  osm_element  one OSM court of the facility being asked about (way/123, node/456)
  label        same       the place is part of the facility that holds that court
               different  that court belongs to another business or facility
  stratum      which part of the sample the pair came from (the sample is stratified, so scores are per stratum)
  evidence     what a public page or the OSM tags say; checked_on = date checked
Keys are place and OSM element ids, not venue_id: venue_id is a hash of the cluster and changes when clusters change.

The model's answer: the place is in the facility when int_place_venue_match links it to the same cluster as the court
(dim_place.matched_venue_id = md5 of the court's cluster_label). Report only: no threshold, nothing fails on a low score.
Because the strata are not random, never quote one blended number as the project's precision.
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "ci" / "gold" / "place_osm_pairs.csv"
DB = ROOT / "courtconnect.duckdb"
LABELS = {"same", "different"}
COLUMNS = ["place_id", "osm_element", "label", "stratum", "evidence", "checked_on"]


def load_gold() -> list[dict]:
    with GOLD.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != COLUMNS:
            sys.exit(f"{GOLD}: columns must be {COLUMNS}")
        rows = list(reader)
    errors, seen = [], set()
    for i, r in enumerate(rows, start=2):
        for c in COLUMNS:
            if not (r[c] or "").strip():
                errors.append(f"line {i}: {c} is empty")
        if r["label"] not in LABELS:
            errors.append(f"line {i}: label must be one of {sorted(LABELS)}")
        key = (r["place_id"], r["osm_element"])
        if key in seen:
            errors.append(f"line {i}: duplicate pair {key}")
        seen.add(key)
    if errors:
        sys.exit("\n".join(errors))
    return rows


def score(rows: list[dict]) -> None:
    import duckdb

    con = duckdb.connect(str(DB), read_only=True)
    # place -> matched venue, court -> cluster venue (same md5 of cluster_label that int_place_venue_match uses)
    place_venue = dict(con.execute("select place_id, venue_id from intermediate.int_place_venue_match").fetchall())
    court_venue = dict(con.execute("select court_id, md5(cluster_label) from intermediate.int_court_clusters").fetchall())
    known_places = {p for (p,) in con.execute("select place_id from core.dim_place").fetchall()}

    tally: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    wrong, stale = [], []
    for r in rows:
        if r["place_id"] not in known_places or r["osm_element"] not in court_venue:
            stale.append(r)
            continue
        predicted_same = place_venue.get(r["place_id"]) is not None and place_venue[r["place_id"]] == court_venue[r["osm_element"]]
        truth_same = r["label"] == "same"
        outcome = ("tp" if predicted_same else "fn") if truth_same else ("fp" if predicted_same else "tn")
        for key in (r["stratum"], "all"):
            tally[key][outcome] += 1
        if outcome in ("fp", "fn"):
            wrong.append((outcome, r, place_venue.get(r["place_id"])))

    print(f"gold pairs: {len(rows)} ({len(stale)} stale: place or court no longer in the warehouse)")
    print(f"{'stratum':<22}{'pairs':>6}{'tp':>5}{'fn':>5}{'fp':>5}{'tn':>5}  precision  recall")
    for key in sorted(tally, key=lambda k: (k == "all", k)):
        t = tally[key]
        n = sum(t.values())
        p = f"{t['tp'] / (t['tp'] + t['fp']):.0%}" if t["tp"] + t["fp"] else "n/a"
        rc = f"{t['tp'] / (t['tp'] + t['fn']):.0%}" if t["tp"] + t["fn"] else "n/a"
        print(f"{key:<22}{n:>6}{t['tp']:>5}{t['fn']:>5}{t['fp']:>5}{t['tn']:>5}  {p:>9}  {rc:>6}")
    print("(strata are not random samples: read each row on its own; 'all' is not the project's precision or recall)")
    if wrong:
        print("\nwrong rows (fix by a rule change, manual_venue_no_merge.csv or a seed):")
        for outcome, r, matched in wrong:
            kind = "MISSED MERGE" if outcome == "fn" else "WRONG MERGE"
            where = f"matched to another venue" if matched else "unmatched"
            print(f"  {kind:<12} {r['place_id'][:8]} {r['osm_element']:<18} [{r['stratum']}, {where}] {r['evidence']}")
    for r in stale:
        print(f"  stale: {r['place_id'][:8]} {r['osm_element']} (rebuild the warehouse, or retire the row)")


def main() -> None:
    rows = load_gold()
    if "--check" in sys.argv:
        print(f"gold match file ok: {len(rows)} pairs, {len({r['stratum'] for r in rows})} strata")
        return
    score(rows)


if __name__ == "__main__":
    main()
