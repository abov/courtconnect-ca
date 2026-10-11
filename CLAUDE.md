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
Phase 1 done: link-outs, confirmation levels (visited/official/reported) with map badges, leads backlog (`venue_leads.csv`), contributor workflow (ADR 0008), table tennis/badminton (ADR 0007). `main` is branch-protected (PR + `dbt-build`; owner can bypass). Build: `.venv/Scripts/dbt build --project-dir transform --profiles-dir transform` (no `make` in Git Bash). Last session (2026-10-10): rejected padel tags at Fox Hills Park, the unnamed court beside it, and Mindanao Way; added lead `mindanao-way-paddle-tennis` (needs a look; paddle tennis = pop tennis).
Next session, one task, in this order:
1. **Private/member clubs** (use public pages only, ADR 0007; no Google Places, ADR 0005). Seed: South End Racquet Club, West End Racquet Club, Manhattan Country Club; check which Equinox locations list racket sports. Then widen to California clubs found via Overture/OSM (`leisure=sports_centre`, `club=sport`), densest areas first (LA, OC, Bay Area, San Diego). Label each as reported/official; say the list is incomplete.
2. **Map access toggle:** three views, public only / private (members) only / both. Use the existing `access` field; keep models engine-neutral; update the app filter and counts.
3. **Directories for the 53 no-data sports:** start with the ~10 most plausible; per sport add a `venue_actions.csv` link-out (keep `verified_on` + `evidence`), a lead, or note "no usable directory". Then refresh `docs/coverage_snapshot.md`.
Other open items: add reviewers as collaborators (owner's call, placeholder wanted); owner to send BracketSync message (`docs/outreach/bracketsync.md`); optional OSM fixes by the owner for the six padel-tagged ways (changeset note: checked on the ground). Unchecked: deploy of `66f8a29`, and the `assert_all_racket_sports_loaded` warning.
