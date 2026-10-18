# 2026-10-17: Census boundaries as a raw reference table

`ingestion/extract_census_boundaries.py` (`make extract-boundaries`) writes `data/raw/census_boundaries.csv` (1,751 CA/NV places + 75 counties as WKT, 4.2 MB, Census 2023, public domain); `load_raw.py` loads it as `raw.census_boundaries` (optional table, so CI fixtures are unaffected). `place_from_boundaries.py` (`make city-boundaries`) now reads that table instead of zips: no download at lookup time.
Cityless pins are 0, so the lookup is a no-op today. Refresh the boundaries yearly at most (next Census release). Runbook step 3 mentions it.
