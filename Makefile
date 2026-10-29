# Windows users: run these from Git Bash, or copy the commands.
PY ?= python
DBT = dbt --project-dir transform --profiles-dir transform
RAW = $(shell $(PY) ingestion/rawdir.py)   # shared raw-CSV folder: the main checkout's data/raw, even from a worktree

setup:            ## one-time: create venv and install deps
	$(PY) -m venv .venv && .venv/bin/pip install -r requirements.txt || .venv/Scripts/pip install -r requirements.txt

extract:          ## pull ALL CalNeva courts + named parent features from OpenStreetMap, then places from Overture (~20 min)
	$(PY) ingestion/extract_osm_courts.py --area california
	$(PY) ingestion/extract_osm_parents.py --area california
	$(PY) ingestion/extract_osm_courts.py --area nevada --out $(RAW)/osm_courts_nv.csv
	$(PY) ingestion/extract_osm_parents.py --area nevada --out $(RAW)/osm_parents_nv.csv
	$(PY) ingestion/extract_overture_places.py
	$(PY) ingestion/extract_overture_addresses.py

fresh-db:         ## new worktree (or a stale/broken db): rebuild courtconnect.duckdb here from the shared raw CSVs + this branch's seeds (~1 min)
	$(PY) ingestion/fresh_db.py

extract-boundaries: ## Census place + county boundaries for CA/NV into data/raw (~13 MB download; yearly at most), then make load
	$(PY) ingestion/extract_census_boundaries.py

city-boundaries: ## city for pins that still have none, from the Census boundaries (writes seeds/venue_place_boundary.csv; then dbt build, make app-data)
	$(PY) ingestion/place_from_boundaries.py

extract-addresses: ## Overture address points near the pins, for the address fill (reads S3, ~1 min; run after the OSM/places extract, then make load)
	$(PY) ingestion/extract_overture_addresses.py

reverse-geocode: ## tier 3 address fill: cached Nominatim lookups for non-home blanks (1 request a second; runs the uncached pins only, capped at 100 per run; ask the owner for more)
	$(PY) ingestion/reverse_geocode_blanks.py --limit 100

extract-places:   ## pull racket-related CalNeva places from Overture Maps (reads S3 directly, ~1 min)
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


app-data:        ## export the venue finder to app/data/venues.json for the map
	$(PY) ingestion/export_app_data.py

changes:         ## diff venues.json with origin/main into app/data/changes.json (public change feed, ADR 0025)
	$(PY) ingestion/build_changes.py

app:             ## serve the map at http://localhost:8765
	$(PY) -m http.server 8765 --directory app

report:           ## regenerate docs/coverage_snapshot.md and docs/sport_name_review.md
	$(PY) ingestion/export_coverage_report.py

check-links:      ## verify every link-out in venue_actions.csv still loads
	$(PY) ingestion/check_action_links.py

rank-review:      ## order the sport review queue, clear-cut cases first -> docs/review_priority.csv (needs requirements-ml.txt)
	$(PY) ingestion/rank_review_queue.py

eval-match:      ## score the Overture place -> OSM match against ci/gold/place_osm_pairs.csv (report only; docs/gold_set_plan.md)
	$(PY) ingestion/eval_match_gold.py

quality:          ## regenerate docs/data_quality.md and append to the trend CSV
	$(PY) ingestion/export_quality_scorecard.py

stats:            ## regenerate app/data/build_stats.json (numbers on app/how-its-built.html); run after make quality
	$(PY) ingestion/build_stats.py

usage:            ## export GoatCounter daily counts and print the usage metrics (needs GOATCOUNTER_API_TOKEN in .env; docs/goat_analysis.md)
	$(PY) ingestion/extract_goatcounter.py
	$(PY) ingestion/goat_report.py $(ARGS)
interest:         ## print Google Trends search interest vs venues per metro (docs/search_interest_plan.md; re-export the seed about quarterly)
	$(PY) ingestion/search_interest_report.py

market-snapshot:  ## append today's venue counts (city x sport) to docs/market_snapshots.csv; run once per refresh after dbt build
	$(PY) ingestion/snapshot_market.py

sync-reports:     ## import approved community-form reports (Google Form) as seed edits; needs REPORTS_CSV_URL in .env
	$(PY) ci/sync_reports.py $(ARGS)

issues:           ## check open GitHub issues: what is missing, already done, duplicate or waiting (needs gh, read-only)
	$(PY) ci/check_issues.py
