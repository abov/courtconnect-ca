# Windows users: run these from Git Bash, or copy the commands.
PY ?= python
DBT = dbt --project-dir transform --profiles-dir transform

setup:            ## one-time: create venv and install deps
	$(PY) -m venv .venv && .venv/bin/pip install -r requirements.txt || .venv/Scripts/pip install -r requirements.txt

extract:          ## pull ALL California courts + named parent features from OpenStreetMap (~10-15 min)
	$(PY) ingestion/extract_osm_courts.py --area california
	$(PY) ingestion/extract_osm_parents.py --area california

extract-la:       ## quick version: Los Angeles only
	$(PY) ingestion/extract_osm_courts.py --area la
	$(PY) ingestion/extract_osm_parents.py --area la

sport-map:        ## rebuild the OSM-tag -> sport mapping from the synced sheet
	$(PY) ingestion/build_osm_sport_map.py

sync-sports:    ## refresh the sports list from the Google Sheet
	$(PY) ingestion/sync_sports_sheet.py

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
