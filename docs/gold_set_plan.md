# Overture/OSM match gold set: plan (first slice built 2026-10-17, see "First slice: result")

Written 2026-10-17. Goal: put a number on how often the pipeline links the wrong things (one pin that should be two, or two pins that should be one), so a change to a radius or a name rule can be judged by a score instead of by eye. Same idea as `ci/check_regions.py` and the review-queue leave-one-out check, aimed at the matching step.

## What is matched today

| Step | Model | Rule (vars in `transform/dbt_project.yml`) | Size now |
|---|---|---|---|
| OSM court -> facility | `int_court_pairs`, `int_court_clusters` | courts within 75 m are one facility; courts inside the same named school/park/club within 400 m too | 27,547 OSM courts -> 10,272 venues |
| **Overture place -> OSM facility** | `int_place_venue_match` | nearest OSM court within 100 m, or within 300 m when place and court have the same lower-cased name | 735 of 1,202 sport places matched |
| Hand-added venue -> known venue | `int_manual_venue_match` | nearest OSM court or strong-sport place within 150 m, unless listed in `manual_venue_no_merge.csv` | 10 known "do not merge" rows |

There is no name-similarity score and no address comparison anywhere: it is distance plus an exact-name shortcut. That is simple and explainable, but two kinds of mistakes are likely and neither is measured:

- **Wrong merge**: a different business within 100 m (the YMCA vs Neighborhood Pickleball case, 100 m apart, is why `manual_venue_no_merge.csv` exists). The match histogram says 55 of 735 matches sit at 75-100 m and 3 use the 300 m same-name rule; that is where wrong merges would hide.
- **Missed merge**: the same club mapped 100+ m apart (a big park, a campus), so we show two pins. 184 unmatched places have an OSM court within about 300 m; 99 are within 200 m.

## Proposal

**Step 1, the slice worth doing first (one session, no new infrastructure beyond one script).** Gold set for the Overture place -> OSM facility step only.

1. File `ci/gold/place_osm_pairs.csv` (not a seed; it is evaluation data, not warehouse input). Columns: `place_id`, `osm_element` (OSM id of one court in the facility, e.g. `way/123`; empty when the label is `none`), `label` (`same` = this place is part of that facility, `different` = this OSM court is another business/facility, `none` = no OSM court in the region is this place), `stratum`, `evidence`, `checked_on`. Keys are place ids and OSM element ids, not `venue_id`, because `venue_id` is a hash of the cluster and changes when clusters change.
2. Sample, stratified (the full 1,202 places are too many to check by hand, and a random sample would be mostly easy cases):
   - 20 matched places at 75-100 m, plus the 3 name-radius matches (suspect precision);
   - 20 unmatched places with an OSM court within 200 m (suspect recall);
   - 10 matched places under 50 m (control, expect all `same`);
   - the 10 `manual_venue_no_merge.csv` pairs as free `different` labels (already evidence-backed).
   About 65 labels.
3. Label from public pages only (CLAUDE.md rules): the place's own website address, the OSM tags/name, Overture address, city park pages. No Google data, no owner logins. Anything that cannot be decided is left out, never guessed (honesty rule).
4. Script `ingestion/eval_match_gold.py` (`make eval-match`, DuckDB only, local like `make rank-review`): for each gold row compare against `int_place_venue_match` / `dim_place.matched_venue_id`.
   - `same` + model puts place in the facility that holds `osm_element` = true positive; `same` + unmatched or other facility = false negative; `different`/`none` + model matched that facility = false positive.
   - Print precision and recall per stratum and overall, and list every wrong row so each failure becomes a rule change or a `manual_venue_no_merge` / seed fix.
   - Report only; no CI threshold at first (the gold set uses real data, CI uses fixtures). Because the sample is stratified, report per stratum and do not quote one blended number as the project's precision.
5. Use: change a radius or add a name rule on a branch, re-run `make build` and `make eval-match`, compare the two reports. This directly answers "is 100 m too tight or too loose".

**Step 2 (after step 1, only if it shows errors worth fixing).** Add a small random sample (about 40 places) so recall and precision can be stated for the whole table with a rough interval. Extend the gold file to `manual_venues` merges (150 m rule) using the merge decisions already recorded in the session notes (YMCA, university and park passes name many correct and wrong merges, so the labels exist and need only collecting).

**Step 3 (later, with the ML phase 2 ADR).** If step 1 shows distance alone is not enough, try a score from distance + name similarity + same city/address token; the gold set is what would let that be evaluated. Do not build the score before there are labels.

## Cheapest first slice

The 20 unmatched places with an OSM court within 200 m plus the 20 matched at 75-100 m: 40 labels, about one review-batch of effort, no schema or dbt change, and it answers both open questions (are we over-merging, are we missing merges). Script is about 40 lines of SQL + Python.

## What this does not cover

OSM-to-OSM clustering (75 m / 400 m) has its own gold need (a school with courts a few hundred metres apart); `assert_clusters_converged` only tests that the algorithm finishes, not that the groups are right. Add it as a second file once step 1 is in place. Sport assignment is separate and already has the review queue and `docs/review_priority.csv`.

## First slice: result (2026-10-17)

Built: `ci/gold/place_osm_pairs.csv` (40 hand-checked pairs), `ingestion/eval_match_gold.py` (`make eval-match`, local DuckDB, report only; CI runs only `--check`, which validates the file format). Labels come from OSM tags (parent polygon or court name, address tags) and public pages, with the evidence written on each row; pairs that could not be decided were left out, so the strata are smaller than planned (12 matched at 75-100 m instead of 20; 19 unmatched instead of 20).

| Stratum | Pairs | Result |
|---|---|---|
| matched 75-100 m | 12 | 12 correct (no wrong merge found) |
| name-radius matches (300 m rule) | 3 | 3 correct |
| matched under 50 m (control) | 6 | 6 correct |
| unmatched, OSM court within 200 m | 19 | **17 missed merges**, 2 correctly unmatched (a table tennis club and an online shop) |

Reading it: no sign of wrong merges, so the 100 m radius is not too loose. The misses are the other direction: places named after the park, school or centre that holds the courts ("Memorial Park Tennis Courts", "Fresno City College Tennis Courts", the Cubberley address) sit 105-182 m from the OSM courts and stay separate pins. Caution: the 19 were picked because their name or address pointed at the facility, so 17 of 19 is not a rate across all unmatched places; it shows the miss is real and has a pattern.

## Next slice (done 2026-10-17, see "Second slice" below; original plan)

1. Try the cheap rule the misses suggest: widen the radius to about 200 m when the place name or address contains the OSM parent's name (park, school, centre; the parent is already in `int_court_parent`) and nothing else is closer. Change it on a branch, run `make build` and `make eval-match`, and see if the 17 misses move without any of the 21 correct pairs breaking.
2. Add the random sample of about 40 places (plan step 2) so a whole-table precision and recall can be stated, and about 10 deliberate `different` pairs for the new rule (two clubs in one park; the YMCA and Neighborhood Pickleball case).

## Second slice: result (2026-10-17)

Rule added to `int_place_venue_match` (third tier `facility_name`, var `place_facility_match_radius_m: 200`; the old two rules win first, so their results are unchanged): a place the old rules leave unmatched joins the nearest OSM court within 200 m when (a) the distinctive part of the place name (generic words such as tennis, courts, club, park, school and single letters removed) equals or contains the court's parent name, or the reverse, 5+ characters; or (b) the place address equals the court's or the parent's address (street suffixes shortened). Golf-course and hotel parents never count for the name test (their bounding boxes swallow neighbours' courts; the Washoe Tennis Club / Washoe Golf Course case). Macros `facility_key` and `address_key` in `cross_db.sql`; `match_rule` column added to the model.

Gold file now 90 pairs, 3 new strata: `facility_rule_new` (16 places the new rule merges, checked), `random_within_300m` (26 labelled out of a seeded random 45 of the 830 places that have an OSM court within 300 m and were not already in the file; 19 skipped because no independent evidence, never guessed), `different_near_courts` (8 offices, events and clubs that share only nearness with courts).

| Stratum | Pairs | Old rule | New rule |
|---|---|---|---|
| matched 75-100 m, name-radius, under 50 m | 21 | 21 correct | 21 correct |
| unmatched, court within 200 m | 19 | 17 missed | 3 missed (Cuesta: different street number; Terra Nova: parent has no address; Stanford: campus name vs "West Campus") |
| facility_rule_new | 16 | 16 missed | 16 correct |
| random_within_300m | 26 | 25 correct, 1 missed | same (the miss is a court 258 m away, outside every radius) |
| different_near_courts | 8 | 8 correct | 8 correct (no wrong merge) |

Effect: 30 places now join an existing venue instead of being separate pins (the map goes from 10,273 to 10,250 venues; the difference is places that had no pin of their own). Read with care: the first two strata were picked knowing what the rule does, so they show it works on the cases it was built for, not a rate. The only unbiased row is the random sample: 0 wrong merges in 26, 1 miss, a small sample (a 95% upper bound on the wrong-merge rate is about 11%). Known soft spot: about a dozen of the 30 new merges are tennis academies or clubs sharing a school's or park's street address; they are treated as part of that facility (their sport is added to the venue). If you would rather keep operators as separate pins, restrict rule (b) to places whose own sport words match the court's sport.

Next: a second random sample (about 40, including places 300 m+ from any court, to catch missed merges the radius hides); pairs skipped for lack of evidence (Rancho Mirage Racquet Club vs The Club at Morningside, 36 m: possibly a wrong merge by the old distance rule) need a public page or an owner report.
