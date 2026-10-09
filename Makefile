# Windows users: run these from Git Bash, or copy the commands.
PY ?= python
DBT = dbt --project-dir transform --profiles-dir transform

setup:            ## one-time: create venv and install deps
	$(PY) -m venv .venv && .venv/bin/pip install -r requirements.txt || .venv/Scripts/pip install -r requirements.txt

extract:          ## pull LA courts from OpenStreetMap
	$(PY) ingestion/extract_osm_courts.py --area la

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
