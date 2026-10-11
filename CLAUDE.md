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
Phase 1 done (link-outs, confirmation levels, leads, contributor workflow, extra sports). `main` is branch-protected (PR + `dbt-build`; owner can bypass). Build: `.venv/Scripts/dbt build --project-dir transform --profiles-dir transform` (no `make` in Git Bash; run it where `courtconnect.duckdb` is, a worktree needs a copy).
Session 2026-10-10 (uncommitted on branch `claude/jolly-turing-7d6584`): (1) access toggle done: `dim_venue.is_members_only` (access private/members, not marked public) -> mart -> export bit 8 -> app "Public / Private-members / Both" (default Both; ~1,457 venues are private/members, mostly OSM `access=private`, incl. residential courts). (2) Seeded South End and Equinox LA/Irvine (official), West End (reported); Manhattan Country Club added with an INFERRED location (18 unmapped OSM tennis courts at Parkview Ave/Village Dr); lead for other Equinox clubs. (3) `docs/sport_directories.md`: only Outdoor Racquetball has a directory (lead `outdoor-racquetball-wor-list`); other 9 sports searched, none found. Coverage snapshot refreshed.
Next: commit/PR this; then widen private clubs via Overture/OSM (the map already holds ~330 named clubs, so the gap is mostly access labels and sports), check the other-Equinox lead, directories pass 2 done 2026-10-10 (docs/sport_directories.md): USA Racquetball court list is link-out only (TeamUSA terms bar copying into a database; rows not read), ~40 sports searched with no usable directory, 10 small ones (listed in the doc) not searched yet. Nothing committed on this branch. Other open items: reviewers as collaborators (owner's call); optional OSM padel fixes by the owner. Unchecked: deploy of `66f8a29`, and the `assert_all_racket_sports_loaded` warning.
