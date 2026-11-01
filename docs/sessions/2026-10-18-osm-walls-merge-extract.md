# 2026-10-18: extract_osm_walls.py merges instead of overwriting

Follow-up to the statewide wall extract: `ingestion/extract_osm_walls.py` now merges into the existing `osm_walls.csv` (same OSM elements replaced, rows outside the queried area kept, rows inside it that OSM no longer returns dropped, nothing dropped if a tile failed). So `--area metros` no longer shrinks a statewide file and the monthly refresh step is safe. Checked with a unit-style test of `merge_rows` and a live `--area carson` run on a scratch copy (890 rows kept).
Next: nothing; city-page wall passes per metro remain the way to add walls.
