# Refresh runbook (run twice a month)

Goal: every venue on the map has been seen by some source in the last 35 days, and the scorecard says so. `make quality` measures it as the service level "Venues seen in the last 35 days" (target >= 99%), from `mart_venue_confidence.last_seen_on`: the newest of the OSM extract date, the Overture release date, a hand-added `confirmed_on` and a link-out `verified_on`. Events age faster and keep their own bi-weekly runbook (`docs/tournament_refresh.md`); private-club events are not checked (parked).

Rules: public pages only, no owner logins (ADR 0007), no Google Places data (ADR 0005), label inferred data as inferred. Cost rules: no subagents, no screenshots, narrow checks before the full build.

## Steps
Run from Git Bash in the main checkout (where `courtconnect.duckdb` is). `make` is not available in Git Bash on this machine; each step shows the target and the command it runs.

1. **Branch.** Fresh `main`, new branch `claude/monthly-YYYY-MM`. Note the last scorecard line in `docs/data_quality_trend.csv`.
2. **Sports sheet (every sync, twice a month).** The Google Sheet and the project must always agree: the sheet is the source of the sports list, so a renamed, added or removed sport lands in the project at each sync, never later. A sport the project needs that the sheet lacks is added to the sheet first (owner), then synced. After syncing, update every place that names a sport (`EXPECTED_SPORTS` in `ingestion/sync_sports_sheet.py` and `expected_racket_sports` in `transform/dbt_project.yml` must equal the sheet count, plus names in `manual_walls.csv`, `sport_also_played.csv` and the generator scripts). `make sync-sports` (`python ingestion/sync_sports_sheet.py`), then `make sport-map` and `make search-terms` if the sheet changed. Never hand-edit `all_racquet.csv` or the generated `osm_sport_map.csv` / `sport_search_terms.csv`.
2b. **Issues (every sync).** `make issues` (`python ci/check_issues.py`, needs `gh` logged in; read-only). For each open issue it lists what is missing, whether the seeds already cite it, duplicates, and issues waiting over 14 days. Act on it: add `approved` to the ones marked ready (issue-to-pr.yml opens the PR), ask reporters for what is missing, make owner reports and corrections by hand in seeds with the issue as evidence, close issues whose PR merged. Note the counts in the PR. The script never comments, labels or closes anything itself.
3. **Extract (ask the owner first, ~15 min).** `make extract` (OSM courts + parents, then Overture places). Overture only: `make extract-places` (~1 min); it picks the newest Overture release, which is what moves the Overture-only venues' `last_seen_on`. Walls (optional, metros only): `python ingestion/extract_osm_walls.py --area metros`. After an OSM or Overture places extract, also run `make extract-addresses` (Overture address points near the pins, ~1 min, reads S3; it reads the pin files in `data/raw`, so run it in the checkout that holds them): `make load` in step 4 then brings the addresses into the warehouse for the address fill. If pins still have no city afterwards, run `make city-boundaries` (Census place / county lookup; reads `raw.census_boundaries`, fill it once with `make extract-boundaries` + `make load`, refresh yearly at most), then `dbt build` and `make app-data`.
4. **Load.** `make load` (`python ingestion/load_raw.py`), and for Snowflake `python ingestion/load_raw.py --target snowflake`.
5. **Link checks.** `make check-links` (link-outs in `venue_actions.csv`; re-date `verified_on` only for rows you re-read) and `make check-websites` (DNS check of venue sites, ~1 min).
6. **Build.** Narrow first if seeds changed (`dbt build --select <changed>+`), then the full `.venv/Scripts/dbt build --project-dir transform --profiles-dir transform` once. Then `make snowflake-build` (add `--full-refresh` where a seed gained a column).
7. **Scorecard and reports.** `make quality` and `make report`. Look at "Stale or undated venues" in `docs/data_quality.md`: give undated hand-added rows a `confirmed_on` only when you re-read their source, otherwise leave them stale (the breach is the honest result) or turn them into a lead.
8. **Export.** `make app-data`, commit `app/data/venues.json` (CI runs `ci/check_export_fresh.py`).
9. **Ship.** Commit, push, open a PR titled `Monthly refresh YYYY-MM`. After it merges, re-run `pages.yml`. Add 2 lines to CLAUDE.md "Current status": date, venues, freshness %, SLAs met.

## What each source contributes to freshness
| Source | Date used | Moves when |
|---|---|---|
| OpenStreetMap courts | `raw.osm_courts.extracted_at` | `make extract` |
| Overture places | `raw.overture_places.release` | `make extract` / `make extract-places` (monthly Overture release) |
| Hand-added venues | `manual_venues.confirmed_on` | someone re-reads the source and re-dates the row |
| Link-outs | `venue_actions.verified_on` | `make check-links` plus a re-read |

A venue known only from an undated reported row has no date and counts as stale until someone confirms it.

## Log
| Month | Venues | Seen in 35 days | SLAs met | Notes |
|---|---|---|---|---|
| 2026-10 (baseline, no refresh run) | 9,941 | 99.9% (9 undated reported rows) | 6 of 7 | OSM extract 2026-10-09, Overture release 2026-09-23 |
