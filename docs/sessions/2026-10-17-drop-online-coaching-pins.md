# 2026-10-17: two online-only coaching pins removed

Pickleball Is Great and Manilla Athletics (Overture places, online coaching, no address, pins in the wrong place) added to `closed_places.csv` with evidence; owner wants venues only. `venues.json` re-exported (10,277 -> 10,275).
Next: county / place boundary file for the last 61 cityless pins (owner to approve the download).

## Follow-up on this branch: city from Census boundaries
`ingestion/place_from_boundaries.py` (DuckDB spatial, Census 2023 place + county cartographic boundary files, public domain) gave the last 59 cityless pins a city: 22 inside a Census place (Kingsbury, El Dorado Hills, Vandenberg AFB, Gerlach...), 37 only a county ("Clark County"). Cached in seed `venue_place_boundary.csv` (lat/lon guard, tests), last tier in `int_venue_address`; no spatial SQL in the model. Cityless pins: 0. Rerun the script after an extract that leaves new cityless pins (needs the three zips from www2.census.gov/geo/tiger/GENZ2023/shp).
