"""Draw a seeded random sample of Overture places for the match gold set (docs/gold_set_plan.md, "Third slice").

    python ingestion/draw_gold_sample.py [--seed 20261018] [--close 12] [--mid 14] [--far 20]

Population: every Overture place in core.dim_place that is not already in ci/gold/place_osm_pairs.csv. Each place is paired with
its NEAREST OSM court (any distance up to 1000 m), then split by what the pipeline did and how far that court is:
  close  the pipeline matched the place to a venue (any rule)               -> precision check
  mid    unmatched, nearest court 100-300 m                                 -> the radius band
  far    unmatched, nearest court 300-1000 m                                -> missed merges the radius hides
Within each bucket the places are sorted by place_id and sampled with random.Random(seed), so the draw is reproducible.
Prints one line per candidate with what a human needs to label it from public/OSM information. Report only; writes nothing.
"""
from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "ci" / "gold" / "place_osm_pairs.csv"
DB = ROOT / "courtconnect.duckdb"

SQL = """
with pl as (
    select p.place_id, p.place_name, p.category, p.lat, p.lon, p.address_line, p.city, p.website, m.venue_id as matched_venue, m.match_rule
    from core.dim_place p
    left join intermediate.int_place_venue_match m on m.place_id = p.place_id
),
cand as (
    select pl.*, c.court_id, c.court_name, c.sport_tag_delimited, c.address_line as court_addr, md5(k.cluster_label) as court_venue,
           sqrt(power((pl.lat - c.lat) * 110540, 2) + power((pl.lon - c.lon) * cos(radians(pl.lat)) * 111320, 2)) as dist_m
    from pl
    join staging.stg_osm_courts c on abs(c.lat - pl.lat) < 0.0095 and abs(c.lon - pl.lon) < 0.0115
    join intermediate.int_court_clusters k on k.court_id = c.court_id
),
nearest as (
    select * from cand qualify row_number() over (partition by place_id order by dist_m, court_id) = 1
)
select n.*, cp.parent_name, cp.parent_kind, pr.address_line as parent_addr
from nearest n
left join intermediate.int_court_parent cp on cp.court_id = n.court_id
left join staging.stg_osm_parents pr on pr.parent_id = cp.parent_id
where n.dist_m <= 1000
order by n.place_id
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20261018)
    ap.add_argument("--close", type=int, default=12)
    ap.add_argument("--mid", type=int, default=14)
    ap.add_argument("--far", type=int, default=20)
    a = ap.parse_args()
    with GOLD.open(newline="", encoding="utf-8") as f:
        have = {r["place_id"] for r in csv.DictReader(f)}
    con = duckdb.connect(str(DB), read_only=True)
    cur = con.execute(SQL)
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall() if r[0] not in have]
    buckets: dict[str, list[dict]] = {"close": [], "mid": [], "far": []}
    for r in rows:
        if r["matched_venue"]:
            buckets["close"].append(r)
        elif r["dist_m"] <= 300:
            buckets["mid"].append(r)
        else:
            buckets["far"].append(r)
    rng = random.Random(a.seed)
    print(f"seed {a.seed}; population (not yet in gold, nearest court <= 1000 m): " + ", ".join(f"{k} {len(v)}" for k, v in buckets.items()))
    for key, n in (("close", a.close), ("mid", a.mid), ("far", a.far)):
        for r in rng.sample(buckets[key], min(n, len(buckets[key]))):
            print(f"\n[{key}] {r['place_id']} | {r['place_name']} | {r['category']} | {r['address_line']}, {r['city']} | {r['website']}"
                  f"\n   rule={r['match_rule']} nearest court {r['court_id']} at {r['dist_m']:.0f} m: '{r['court_name']}' sport={r['sport_tag_delimited']}"
                  f" addr={r['court_addr']} | parent={r['parent_name']} ({r['parent_kind']}) addr={r['parent_addr']}")


if __name__ == "__main__":
    main()
