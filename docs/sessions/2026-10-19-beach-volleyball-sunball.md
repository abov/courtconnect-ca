# 2026-10-19 Beach / sand volleyball courts as Pro Sunball candidates

Added `ingestion/extract_osm_beach_volleyball.py` (OSM `sport=beachvolleyball`, plus `volleyball` on sand/beach surface; CA + NV, clipped to borders). Output `data/raw/osm_beach_volleyball.csv` (not loaded into dbt): 1,527 court elements = about 841 sites within 150 m (787 CA, 54 NV); 669 sites have 1 court, 31 have 6+; only 42 sites are named and 2 rows have a city. Pro Sunball itself still has no venues or OSM tag, so every row is an inferred candidate, never a confirmed venue.

Next (owner's call): load as a candidate layer (dbt model + labelled "inferred" in the app, ADR first if it adds a new sport source), fill city via `place_from_boundaries.py`, keep only public/`access` != private. Run `fresh_db` is not needed until then.
