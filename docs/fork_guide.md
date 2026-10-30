# Fork guide: run this for your own area or sport

Status: draft (2026-10-29). The region config was moved out of code and checked to give the same values as before. Steps 1 and 2 now have a script (`ingestion/init_fork.py`, below). On a scratch copy I ran it for a made-up Texas region and built the CI fixture data with dbt: 333 nodes passed, 1 test failed and 7 nodes were skipped; the failure is `assert_padel_has_supporting_signal`, which needs the California research seeds the script empties (swap `ci/fixtures` for your own area to get a meaningful result). A real extract for another area has not been tried, so treat the rest as a checklist and fix what you hit.

The code is MIT (`LICENSE`). The data keeps its own licenses: keep the notices in `NOTICE.md` (OpenStreetMap is ODbL, Overture is mostly CDLA-Permissive-2.0). Do not store Google Places content (ADR 0005).

## What you get

Python ingestion -> dbt on DuckDB -> one `app/data/venues.json` -> a static MapLibre page. No server, no accounts, no paid service needed. Every pin carries a confirmation level, and inferred data is labelled as inferred. Seed edits need `evidence` + `verified_on`, so changes are reviewable.

## Quick start: `init_fork.py` does steps 1 and 2

```bash
python ingestion/init_fork.py --region TX texas 25.8 -106.7 36.6 -93.5 114690            # dry run: lists every change
python ingestion/init_fork.py --region TX texas 25.8 -106.7 36.6 -93.5 114690 --apply    # does it (needs a clean git tree)
```

`--region CODE NAME SOUTH WEST NORTH EAST OSM_RELATION` can repeat; `--metro KEY S W N E CODE` adds a named sub-area for quick runs. It rewrites `ingestion/regions.json` and empties the CA/NV research seeds, keeping the header rows (the dbt config pins their columns as text, so empty files build). It does not touch the mapping seeds, `ci/gold`, `ci/fixtures`, the sports sheet or your keys; it prints what is left. To use this repo as a starting point on GitHub, mark it a template repository in its settings (the owner's decision), then run the script in your copy. Tested offline by `ci/test_init_fork.py`.

## 1. Set your area (one file)

Edit `ingestion/regions.json`:

- `regions`: one entry per state/province/country part. `bbox` is south, west, north, east. `relation` is the OSM relation id of its border (find it on openstreetmap.org: the relation page, `admin_level` boundary). `name` is the `--area` value (for example `california`). `cache` is the border file saved under `data/raw`.
- `metros`: named sub-areas for quick runs (`--area la`), with the regions each may keep rows from.

Check the clip with your own test points in `ci/check_regions.py` (replace the CA/NV points with places inside and outside your area), then run `python ci/check_regions.py`.

## 2. Replace the CA/NV research

These seeds hold the original owner's research for California and Nevada. Empty them (keep the header row) or replace them with your own:

`manual_venues`, `manual_walls`, `venue_actions`, `venue_confirmations`, `venue_leads`, `watch_events`, `social_events`, `player_groups`, `closed_places`, `venue_court_counts`, `place_sport_overrides`, `osm_court_sport_overrides`, `venue_*_official`, `website_overrides`, `nominatim_addresses`, `venue_place_boundary`, `search_interest`, `search_metros`.

Keep the mapping seeds (`osm_sport_map`, `overture_category_map`, `sport_aliases`, `sport_search_terms`) and adjust them for your sports. `ci/gold/` and `ci/fixtures/` are CA/NV samples too: swap them or the match-evaluation check will not mean anything for you.

## 3. Your sports list

`make sync-sports` overwrites `all_racquet.csv` from the owner's private Google Sheet. For a fork, skip that target and edit `transform/seeds/all_racquet.csv` directly (or point `SPORTS_SHEET_ID` at your own sheet). The columns are described in `docs/sport_discovery_plan.md`.

## 4. Identity and keys

- `COURTCONNECT_USER_AGENT` (env): your project name and public URL, sent to outside services. Never use a personal email in it. The default is this project's.
- `.env` (copy `.env.example`, never commit it): everything is optional. `GOATCOUNTER_API_TOKEN` is only for usage numbers, `ANTHROPIC_API_KEY` only for the page-reader pilot, `REPORTS_CSV_URL` only for the community report form.
- `app/index.html`: title, social tags, logo and the analytics site code (`GOATCOUNTER_CODE`; leave it empty to run with no analytics).
- `.github/workflows/pages.yml`: set up GitHub Pages for your repo.

## 5. First run

```bash
make setup
make extract     # about 15-20 minutes; use --area <metro> in the extract scripts for a quick trial
make load
make build
make app-data
make app         # http://localhost:8765
```

## Known leftovers (still CA/NV specific)

- `ingestion/ask.py` rejects regions other than CA/NV; `ingestion/export_coverage_report.py` has a Nevada-specific sentence.
- The Census boundary and place-name steps (`make extract-boundaries`, `make city-boundaries`, `ingestion/build_places_lookup.py`) are US-only. Outside the US, replace the city source.
- Some docs and the About card text describe California and Nevada.
- Scheduled tasks and the agent workflows (refresh, issue triage) are tied to the owner's accounts. Leave them out until you have your own.

## Rules worth copying, and rules that are the owner's choice

Worth copying: label inferred data as inferred, require evidence + date on every manual edit, link out and take no bookings or payments, keep a freshness check in CI.

Specific to the original owner (drop or replace): the no-partnership-emails rule, "never use the owner's logins", and the CA/NV scope decisions in `docs/decisions/`.
