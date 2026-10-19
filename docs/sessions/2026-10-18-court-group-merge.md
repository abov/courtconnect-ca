# 2026-10-18: merge duplicate court groups (follow-up to the named-venues pass)

New seed `court_group_merge.csv` (OSM court id pairs, evidence + `verified_on`, relationship tests) feeds `int_court_pairs`, so a club's court groups mapped 78-131 m apart become one venue: 7 duplicates merged (Avendale, Country Swim & Racquet, Orindawoods, Oakland Hills, Hills Swim & Tennis, Carmel Valley Tennis Camp, Knowlwood). Venues 10,248 -> 10,241; real-name share stays 14.2%.
Not merged: Quail Lakes Racquet Club (the named side is an Overture place with no OSM courts, so there is no court to pair with; its unnamed group stays unnamed). Merges are by position, club pages not read.
Next: only more of the same kind if cheap; the real-name target needs the park/school naming decision (see 2026-10-18-named-venues-pass.md).
