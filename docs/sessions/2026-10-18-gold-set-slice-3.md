# 2026-10-18 gold set slice 3 (second random sample)

Gold file 90 -> 121 pairs: seeded random sample (seed 20261018, `ingestion/draw_gold_sample.py`) incl. places 300 m+ from any court. 0 wrong merges before and after; missed merges 13 -> 11. Rule change: `place_facility_match_radius_m` 200 -> 300 with a bare-city-name guard (it caught a real wrong merge, Atascadero Pickleball Club); 11 more places join venues (10,248 -> 10,237 pins, `venues.json` re-exported). Details and numbers in `docs/gold_set_plan.md`, "Third slice".
Next: the footprint rule for the 7 remaining misses (proposed in the plan, review the list of new merges first); Fountain Valley Tennis Center pin looks misplaced.
