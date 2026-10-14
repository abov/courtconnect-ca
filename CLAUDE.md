# CourtConnect California

Racket-sport venue finder for California: Python ingestion -> dbt (DuckDB dev/CI, Snowflake prod) -> static MapLibre map in `app/`.
README.md has the full story; read it only if you need background. Decisions are in `docs/decisions/` (ADRs 0001-0014, all accepted; one file each, read only the one you need).

## Commands (run from Git Bash on Windows)
- `make build`      dbt seeds + models + tests (the main check; run after any change to `transform/`)
- `make app-data`   export `app/data/venues.json` for the map (commit it after any seed change; CI runs `ci/check_export_fresh.py`); `make app` serves it at localhost:8765
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
- In auto mode (or whenever I haven't picked an approach), always choose the cheapest path that does the job, and say in one line what it is:
  - Do it directly with Grep/Read/Edit; don't spawn subagents, run deep-research, or use extended web search unless I ask.
  - Run the narrowest check (`dbt build --select <changed models>`, one test) before the full build; run the full build once at the end.
  - Never start `make extract`/`make load`/`snowflake-build`, or loops/scheduled tasks, without asking.
  - Prefer one batched tool call over many; stop once the task is done instead of extra "nice to have" work.
  - If a task looks expensive (many pages to research, big refactor), propose the cheaper scoped version first and wait for my OK.
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
Full session log (2026-10-10 .. 10-14): `docs/status_history.md`. Plan: `~/.claude/plans/create-a-revised-plan-temporal-yao.md`. Add one short dated line per session here; move old lines to the history file when this passes ~15 lines.

**Working practices**
- Build: `.venv/Scripts/dbt build --project-dir transform --profiles-dir transform` (no `make` in Git Bash). A worktree needs a copy of `courtconnect.duckdb`.
- Seed column changes need `--full-refresh` (Snowflake too). New raw tables need `load_raw.py --target snowflake`. Sync Snowflake after every DuckDB change.
- Commit `app/data/venues.json` after `make app-data`. Re-run `pages.yml` after merging any app/export change; check the latest run (another session's run cancels yours). Confirm a PR is MERGED before calling it shipped.
- Dirty main checkout: `git worktree add ../x -b branch origin/main`, use the main `.venv`, copy `.env` only for the Snowflake build, then delete it.

**Done (summary):** CA map with link-outs, confirmation levels, leads, suggest-a-change form -> PR workflow (ADR 0008), social/WhatsApp/Meetup/Partiful link-outs (ADR 0009/0010/0012), OSM edit link (ADR 0011), GoatCounter analytics (ADR 0013, site `courts`), logo C, UX Option A PRs 1-3, 43 tournament events, 265 hitting walls (LA/SD/Bay OSM + 2 owner), private-club passes 1-2 (partial), `ref_sport_fit`, `mart_sport_evidence`, `mart_venue_confidence` rules_v2 (not exported), `make quality` scorecard incl. 35-day freshness SLA, monthly runbook, ADR 0014 CalNeva step 1 (`REGIONS` in `ingestion/overpass.py`, `ci/check_regions.py`).

**Open, in order**
1. CalNeva (ADR 0014): step 2 done (`region` column); next the label rename PR (step 3), Nevada metro extracts (ask first), Nevada seeds/runbook rows.
2. Beta round (docs/feedback_round.md): replies due 10-28, findings 10-29..11-01, then fill case study + docs/feedback_findings.md (RICE). Owner: exclude own IP in GoatCounter.
3. Accuracy: confidence band counts in `make quality`, Overture/OSM match gold set, clear the 249-row review queue from public pages.
4. Small: Sunset Padel LA website -> `website_overrides`; owner to confirm Basque Pelota (Chino trinquet, South SF center); owner review of UX live.
5. Coverage: `*-access` leads, ~440 club-named venues (pass 2 parked), beach tennis court locations from clubs, statewide walls (parked), NorCal Equinox, OSM fix list (optional).
6. Recheck: Club Locker (squash), Cosm events, badminton 2027 ORCs (Nov-Dec).
7. LATER (after beta): optional read-only CourtConnect MCP server over `venues.json` (details in docs/status_history.md, TODO 2026-10-14; ADR first).

**Sessions**
- 2026-10-14c: CalNeva step 2 merged (#67, Pages redeployed): `region` CA/NV through raw -> dims -> mart -> export `r`; Overture's address state is `address_region`; bbox tests are `assert_*_inside_region`. All 9,941 venues CA. A parallel duplicate (#70) was closed.
- 2026-10-14d: status log moved to docs/status_history.md (this section trimmed).
