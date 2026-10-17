# Overture/OSM match gold set: plan (proposal, nothing built yet)

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
