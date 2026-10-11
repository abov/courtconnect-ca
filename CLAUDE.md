# CourtConnect California

Racket-sport venue finder for California: Python ingestion -> dbt (DuckDB dev/CI, Snowflake prod) -> static MapLibre map in `app/`.
README.md has the full story; read it only if you need background. Decisions are in `docs/decisions/` (ADRs 0001-0006).

## Commands (run from Git Bash on Windows)
- `make build`      dbt seeds + models + tests (the main check; run after any change to `transform/`)
- `make app-data`   export `app/data/venues.json` for the map; `make app` serves it at localhost:8765
- `make extract` / `make load`   refresh raw data (extract takes ~15 min; don't run unless asked)
- `make check-links` / `make check-websites`   verify link-outs / flag dead venue sites
- `make report`     regenerate `docs/coverage_snapshot.md`
- `make snowflake-build`   same project on Snowflake (needs credentials in `.env`)

## Rules
- NEVER read, print or commit `.env` (credentials). `.env.example` shows the keys.
- Never hand-edit `transform/seeds/all_racquet.csv` or Snowflake `RAW.ALL_RACQUET`: the Google Sheet is the source, `make sync-sports` overwrites them.
- Data edits go in seeds, then `make build`:
  - `manual_venues.csv` (venues no dataset knows), `venue_actions.csv` (link-outs; keep `verified_on` + `evidence`),
  - `watch_events.csv` (https links only), `place_sport_overrides.csv` (confirm/reject uncertain matches), `sport_aliases.csv`.
- Models must run unchanged on DuckDB and Snowflake: use `adapter.dispatch` macros, no engine-specific SQL.
- Honesty over polish: label inferred data as inferred, never present guesses as confirmed. CourtConnect links out; it takes no bookings or payments.
- NEVER use the owner's logins (Playtomic, PlayByPoint, Padel Up, etc.) or read logged-in pages; use public pages and what the owner reports (ADR 0007).
- Don't use Google Places data (terms forbid storing it); Overture + OSM only (ADR 0005).
- Ignore generated/bulky paths when searching: `transform/target`, `transform/logs`, `courtconnect.duckdb`, `app/data/venues.json`.

## Keeping usage low
- Don't take browser screenshots unless I ask. Read pages as text (`get_page_text` / `read_page`) instead.
- Read only the lines you need from big files; don't dump whole CSVs, logs or `venues.json`.
- One task per session. Keep sessions small: when context passes ~200-300k tokens, update "Current status" below and tell me to start a fresh session.
- At the end of a session, update "Current status" (2-3 lines) so the next session can pick up without a long history.
- Use a lighter model for simple edits; save the biggest for hard problems.

## Where things are
- `ingestion/`   Python extract/load/export scripts
- `transform/`   dbt project (models, seeds, macros, tests)
- `app/`         static map page
- `ci/fixtures`  small sample data for CI

## Current status
Phase 1 done, plus padel/beach tennis link-outs, platform tennis lead, confirmation levels (visited/official/reported) with map badges,
a leads backlog (`venue_leads.csv`, `mart_venue_leads`), a "Report a venue" issue form, and table tennis/badminton additions (ADR 0007).
Committed (fd329db), CI green, and deployed via `pages.yml` on 2026-10-11.
MIT `LICENSE` added (code only; data terms stay in NOTICE.md) and BracketSync message drafted in `docs/outreach/bracketsync.md` (unsent).
Next: more link-outs, directories for the 53 no-data sports; send the BracketSync message.
