# 2026-10-18 gold set: footprint rule

New `inside_facility` tier in `int_place_venue_match` (lesson/court records whose pin is inside a small park/school/centre footprint, court within 350 m; clubs, resorts, gyms, leagues and human-rejected places excluded). 28 places join venues; whole gold file (129 pairs) 21 -> 4 missed merges, 0 wrong. Gold label for Itennis (Andulka Park) corrected to `same`; Fountain Valley misplaced duplicate pin dropped via `closed_places.csv`. `venues.json` re-exported. Details: `docs/gold_set_plan.md`, "Fourth slice".
Next: re-run `make eval-match` after the next OSM refresh (parent boxes change); La Costa, Quail Lakes, Better At Pickleball and Stanford West Campus stay unmatched.
