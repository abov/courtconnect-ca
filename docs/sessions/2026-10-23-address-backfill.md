# 2026-10-23: address backfill (queue item 2)

No new extract or OSM refresh since 2026-10-17, but pins added since then left 35 non-home blanks: `reverse_geocode_blanks.py` cached all 35 (Nominatim, project User-Agent, pin coordinates only), `dbt build` passes, `venues.json` re-exported. Result: 20 pins gain an inferred street (`ai`), 14 gain a "Near <street>" road (`ns`); home-like pins untouched.
Next: rerun `reverse_geocode_blanks.py` (+ `extract_osm_parents.py` after an OSM refresh) after the next extract.
