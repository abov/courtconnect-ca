# 2026-10-23 gold set re-run: skipped (no OSM refresh)

No OSM refresh since the 2026-10-18 measurement (`osm_courts*.csv` 2026-10-14, `osm_parents*.csv` 2026-10-17 in the shared `data/raw`; matching rules unchanged since #235), so `make eval-match` was not re-run. Standing result: 129 pairs, 0 wrong merges, 4 missed.
Next: after the next OSM refresh, run `python ingestion/fresh_db.py` then `make eval-match` and compare with 0 wrong / 4 missed.
