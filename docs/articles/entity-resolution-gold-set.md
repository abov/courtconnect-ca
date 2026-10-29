# Measuring entity resolution with a gold set of 129 pairs

*Draft, 2026-10-29. Every number below comes from [`docs/gold_set_plan.md`](../gold_set_plan.md) or from `make eval-match`; the file and script are in the repo.*

CourtConnect joins two maps that disagree. OpenStreetMap (OSM) knows where the courts are but rarely names them. Overture Maps knows business names but not courts. The product is the join: "this Overture place is the club that runs those OSM courts".

For weeks the join had no score. It was distance plus one shortcut (a place within 100 m of a court, or within 300 m if the two share an exact name), and I tuned it by looking at the map. That fails quietly. Two mistakes are possible and neither shows up in a row count: gluing together two businesses that are only neighbours, or leaving one club as two pins because its courts sit across a park.

So I put a number on it.

## The gold set

A gold set is a small file of pairs a person has checked. Each row of [`ci/gold/place_osm_pairs.csv`](../../ci/gold/place_osm_pairs.csv) says: this place and this OSM court are the `same` facility, or they are `different`, with the evidence written on the row and the date checked.

Three rules shaped it:

- **Keys that do not move.** Rows use the Overture place id and the OSM element id, not our `venue_id`, because `venue_id` is a hash of a cluster and changes whenever clusters change.
- **Stratified, not random.** The full table was too large to label and a random sample is mostly easy cases. I drew samples from the places where mistakes would hide: matches at 75–100 m, unmatched places with a court nearby, and a control group of obvious matches.
- **No guessing.** Public pages and OSM tags only, and anything I could not decide was left out. Of 46 candidates in one draw, 14 were skipped for lack of independent evidence.

The script, [`ingestion/eval_match_gold.py`](../../ingestion/eval_match_gold.py), compares each row with what the warehouse decided and prints wrong merges and missed merges per stratum. It reports and never fails a build, because CI only has a small fixture dataset; CI checks that the file is well formed and the score runs locally.

## What the first 40 labels showed

The worry was wrong merges. There were none: all 12 matches at 75–100 m were right, as were the three name-radius matches and the six controls.

The problem was on the other side. Of 19 unmatched places that had an OSM court within 200 m, 17 were missed merges. Places named after the park or school that holds the courts ("Memorial Park Tennis Courts") sat 105–182 m from the courts and stayed as separate pins. Those 19 were picked because their names pointed at the facility, so 17 of 19 is not a rate across the table. It showed the miss was real and had a pattern.

## Three rule changes, each judged by the score

1. **A facility-name rule at 200 m.** A place joins a court when the distinctive part of its name matches the court's park, school or centre, or when their addresses match. Golf-course and hotel parents never count, because their bounding boxes swallow neighbours' courts. On the random sample the rule made 0 wrong merges in 26, with one miss. With a sample that small the 95% upper bound on the wrong-merge rate is about 11%, so I wrote that down too.
2. **Radius 200 m to 300 m, plus a city-name guard.** A second random sample (seeded, so it can be redrawn) showed raising the radius would have joined Atascadero Pickleball Club to a school-district court because both names contain the city. It was caught before shipping and added to the file as a `different` pair. The first version of my guard then broke a correct match ("Tustin Sports Park"), and the gold set caught that as well.
3. **A footprint tier.** A place whose pin lies inside a small park or school footprint, with a racquet-sport category, joins that facility. A dry run of the naive version on 72 candidates would have merged a racquet club into the park beside it and a resort into a neighbouring park, so clubs, resorts and gyms are excluded.

On the 129-pair file the footprint tier moves missed merges from 21 to 4. Wrong merges stay at 0. Re-run on 2026-10-29 after a refresh, it was unchanged.

## What this does not prove

- **There is no single precision number.** The strata were chosen, some knowing what a rule does, so a blended score would flatter it. The only unbiased rows are the random ones: 0 wrong in 38 across the random samples, with an upper bound near 8%.
- **The labels are mine and the sample is small.** I could be wrong about a pair, which is why every row carries its evidence.
- **Four misses remain.** Some are an HOA with no parent, a park nickname or a school renamed in OSM. They are listed, not hidden.
- **One pair is still undecided.** A distance-rule merge at 36 m might be wrong, and I have no public page to settle it.

## What I would take from this

- A score changes the conversation from "this looks better" to "missed merges fell from 21 to 4 and wrong merges stayed at 0".
- The labels were worth more than the rules. The data came from reading real clubs, and each pair turned a guess into a test.
- Build the gold set before the clever model. The next step, a learned similarity score, only makes sense now that there are labels to judge it.

*Reproduce: `make fresh-db`, then `make eval-match`. Plan and every slice's result: [`docs/gold_set_plan.md`](../gold_set_plan.md).*
