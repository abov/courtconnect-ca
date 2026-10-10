# Windows users: run these from Git Bash, or copy the commands.
PY ?= python
DBT = dbt --project-dir transform --profiles-dir transform

setup:            ## one-time: create venv and install deps
	$(PY) -m venv .venv && .venv/bin/pip install -r requirements.txt || .venv/Scripts/pip install -r requirements.txt

extract:          ## pull ALL California courts + named parent features from OpenStreetMap, then places from Overture (~15 min)
	$(PY) ingestion/extract_osm_courts.py --area california
	$(PY) ingestion/extract_osm_parents.py --area california
	$(PY) ingestion/extract_overture_places.py

extract-places:   ## pull racket-related California places from Overture Maps (reads S3 directly, ~1 min)
	$(PY) ingestion/extract_overture_places.py

search-terms:     ## rebuild the sport name-keyword list (used to find places by business name)
	$(PY) ingestion/build_search_terms.py

extract-la:       ## quick version: Los Angeles only
	$(PY) ingestion/extract_osm_courts.py --area la
	$(PY) ingestion/extract_osm_parents.py --area la

sport-map:        ## rebuild the OSM-tag -> sport mapping from the synced sheet
	$(PY) ingestion/build_osm_sport_map.py

sync-sports:    ## refresh the sports list from the Google Sheet
	$(PY) ingestion/sync_sports_sheet.py

check-websites: ## flag venue websites whose domain no longer exists (DNS only, ~1 min)
	$(PY) ingestion/check_websites.py

load:             ## load raw CSV into DuckDB
	$(PY) ingestion/load_raw.py

build:            ## seeds + models + tests
	$(DBT) build

demo: extract load build   ## the one-command demo
	@echo "Done. Try: duckdb courtconnect.duckdb 'select * from marts.mart_sport_coverage'"

docs:
	$(DBT) docs generate && $(DBT) docs serve

snowflake-build:  ## run the same project on Snowflake
	$(PY) ingestion/load_raw.py --target snowflake
	$(DBT) build --target snowflake

app-data:        ## export the venue finder to app/data/venues.json for the map
	$(PY) ingestion/export_app_data.py

app:             ## serve the map at http://localhost:8765
	$(PY) -m http.server 8765 --directory app

report:           ## regenerate docs/coverage_snapshot.md and docs/sport_name_review.md
	$(PY) ingestion/export_coverage_report.py
