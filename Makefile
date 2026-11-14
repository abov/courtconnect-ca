# Windows users: run these from Git Bash, or copy the commands.
PY ?= python
DBT = dbt --project-dir transform --profiles-dir transform
STATES = $(shell $(PY) -c "import sys; sys.path.insert(0, 'ingestion'); import overpass; print(*overpass.DEFAULT_AREAS)")   # --area value of every covered state (ingestion/regions.json; regions marked defer, like Mexico, are left out)
RAW = $(shell $(PY) ingestion/rawdir.py)   # shared raw-CSV folder: the main checkout's data/raw, even from a worktree

# Without this, `make app` and `make docs` see the app/ and docs/ directories and report "up to date".
.PHONY: rank-rechecks check-pages setup extract fetch-data fresh-db extract-boundaries extract-boundaries-mx city-boundaries extract-addresses reverse-geocode extract-places search-terms extract-walls extract-la sport-map sync-sports check-websites load deps build build-changed observability ops-metrics demo refresh docs app-data changes app report check-links rank-review eval-match quality dashboard-data stats usage interest market-snapshot sync-reports issues feedback ask-feedback

setup:            ## one-time: create venv and install deps
	$(PY) -m venv .venv && .venv/bin/pip install -r requirements.txt || .venv/Scripts/pip install -r requirements.txt

extract:          ## pull ALL courts for every state in regions.json + named parent features from OpenStreetMap, then places from Overture (~20 min)
	for a in $(STATES); do $(PY) ingestion/extract_osm_courts.py --area $$a && $(PY) ingestion/extract_osm_parents.py --area $$a || exit 1; done   # California -> osm_courts.csv, other states -> osm_courts_<code>.csv
	$(PY) ingestion/extract_overture_places.py
	$(PY) ingestion/extract_overture_addresses.py

fetch-data:        ## download the public raw-data bundle (GitHub Release) into data/raw instead of running the extract; then make fresh-db
	$(PY) ingestion/fetch_data_bundle.py

fresh-db:         ## new worktree (or a stale/broken db): rebuild courtconnect.duckdb here from the shared raw CSVs + this branch's seeds (~1 min)
	$(PY) ingestion/fresh_db.py

extract-boundaries: ## Census place + county boundaries for CA/NV into data/raw (~13 MB download; yearly at most), then make load
	$(PY) ingestion/extract_census_boundaries.py

extract-boundaries-mx: ## Mexican municipio + locality boundaries from Overture divisions into data/raw (~10 MB, 15 s; ADR 0034; not part of make extract), then make load
	$(PY) ingestion/extract_overture_boundaries.py

city-boundaries: ## city for pins that still have none, from the Census boundaries (writes seeds/venue_place_boundary.csv; then dbt build, make app-data)
	$(PY) ingestion/place_from_boundaries.py

extract-addresses: ## Overture address points near the pins, for the address fill (reads S3, ~1 min; run after the OSM/places extract, then make load; ARGS="--region HI" for one new state only)
	$(PY) ingestion/extract_overture_addresses.py $(ARGS)

reverse-geocode: ## tier 3 address fill: cached Nominatim lookups for non-home blanks (1 request a second; runs the uncached pins only, capped at 100 per run; ask the owner for more)
	$(PY) ingestion/reverse_geocode_blanks.py --limit 100

extract-places:   ## pull racket-related places from Overture Maps (reads S3 directly, ~1 min; ARGS="--region HI" for one new state only, other states' rows stay)
	$(PY) ingestion/extract_overture_places.py $(ARGS)

search-terms:     ## rebuild the sport name-keyword list (used to find places by business name)
	$(PY) ingestion/build_search_terms.py

extract-walls:    ## hitting walls (1-wall backboards, 3-wall handball) for every covered state (owner 2026-11-02; NOT part of make extract; ~10-20 min per big state)
	for a in $(STATES); do $(PY) ingestion/extract_osm_walls.py --area $$a || exit 1; done

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

deps:             ## install dbt packages (Elementary); needed once per checkout
	$(DBT) deps

build: deps       ## seeds + models + tests
	$(DBT) build

build-changed:    ## only what changed since the last good build + downstream (falls back to a full build; ARGS=--full or --dry-run; not for raw-data loads)
	$(PY) ingestion/build_changed.py $(ARGS)

observability:    ## Elementary report from the local warehouse (docs/data_observability.md); run make build first
	$(PY) ingestion/observability_report.py

ops-metrics:      ## merged PRs/day, conflict-commit signal, CI/Pages durations, slowest dbt models, Claude token use (docs/ops_metrics.md; needs gh; ARGS="--days 7 --only prs,runs")
	$(PY) ingestion/ops_metrics.py $(ARGS)

demo: extract load build   ## the one-command demo
	@echo "Done. Try: duckdb courtconnect.duckdb 'select * from marts.mart_sport_coverage'"

refresh:          ## after make extract (docs/monthly_refresh.md steps 4, 6-8a): load, build, address fill, rebuild, scorecard, stats, reports, export, change feed; stops at the first failure
	$(MAKE) load
	$(MAKE) build
	$(MAKE) reverse-geocode
	$(MAKE) build-changed
	$(MAKE) quality
	$(MAKE) stats
	$(MAKE) report
	$(MAKE) market-snapshot
	git fetch --no-tags origin main
	$(PY) ci/check_scorecard_regression.py --base-ref origin/main
	$(MAKE) app-data
	$(MAKE) changes
	@echo "Refresh done. Still by hand: sync-sports, issues, check-links, social series, sport of the month (app/data/featured_sport.json), then commit and open the PR (docs/monthly_refresh.md)."

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

check-pages:      ## list verified pages that changed or vanished since the last look (conditional requests + text hash; ARGS="--limit 50")
	$(PY) ingestion/check_page_changes.py $(ARGS)

rank-rechecks:    ## rank venues by expected harm (traffic x chance it changed) -> docs/recheck_queue.csv; ARGS="--top 100" or ARGS="--budget-usd 2" (docs/recheck_queue_plan.md)
	$(PY) ingestion/rank_rechecks.py $(ARGS)

check-links:      ## verify every link-out in venue_actions.csv still loads
	$(PY) ingestion/check_action_links.py

rank-review:      ## order the sport review queue, clear-cut cases first -> docs/review_priority.csv (needs requirements-ml.txt)
	$(PY) ingestion/rank_review_queue.py

eval-match:      ## score the Overture place -> OSM match against ci/gold/place_osm_pairs.csv (report only; docs/gold_set_plan.md)
	$(PY) ingestion/eval_match_gold.py

quality:          ## regenerate docs/data_quality.md and append to the trend CSV
	$(PY) ingestion/export_quality_scorecard.py

dashboard-data:   ## aggregate CSVs for the Evidence.dev dashboard (dashboard/README.md); run after make quality, stats, app-data
	$(PY) ingestion/export_dashboard_data.py

stats:            ## regenerate app/data/build_stats.json (numbers on app/how-its-built.html); run after make quality
	$(PY) ingestion/build_stats.py

usage:            ## export GoatCounter daily counts (and roll up docs/usage_daily.csv and docs/usage_events.csv for the dashboard; commit them) and print the usage metrics (needs GOATCOUNTER_API_TOKEN in .env; docs/goat_analysis.md)
	$(PY) ingestion/extract_goatcounter.py
	$(PY) ingestion/usage_daily.py
	$(PY) ingestion/goat_report.py $(ARGS)
ask-feedback:     ## load the questions visitors sent from the ask box into raw.ask_feedback and build mart_ask_feedback (run `make usage` first; local warehouse only, never commit the text; docs/goat_analysis.md)
	$(PY) ingestion/extract_ask_feedback.py
	$(PY) ingestion/load_raw.py
	$(DBT) build --select stg_ask_feedback mart_ask_feedback
interest:         ## print Google Trends search interest vs venues per metro and write docs/search_interest_vs_coverage.csv for the dashboard (docs/search_interest_plan.md; re-export the seed about quarterly)
	$(PY) ingestion/search_interest_report.py

market-snapshot:  ## append today's venue counts (city x sport) to docs/market_snapshots.csv; run once per refresh after dbt build
	$(PY) ingestion/snapshot_market.py

sync-reports:     ## import approved community-form reports (Google Form) as seed edits; needs REPORTS_CSV_URL in .env
	$(PY) ci/sync_reports.py $(ARGS)

issues:           ## check open GitHub issues: what is missing, already done, duplicate or waiting (needs gh, read-only)
	$(PY) ci/check_issues.py

feedback:         ## sync all GitHub issues (open + closed) into docs/feedback_log.csv and list open/handled feedback (needs gh)
	$(PY) ci/feedback_log.py $(ARGS)
