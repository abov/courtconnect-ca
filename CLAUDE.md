# CourtConnect CalNeva

Racket-sport venue finder for California + Nevada ("CalNeva", ADR 0014): Python ingestion -> dbt (DuckDB dev/CI, Snowflake prod) -> static MapLibre map in `app/`.
README.md has the full story; read it only if you need background. Decisions are in `docs/decisions/` (ADRs 0001-0014, all accepted; one file each, read only the one you need).

## Commands (run from Git Bash on Windows)
- `make build`      dbt seeds + models + tests (the main check; run after any change to `transform/`)
- `make app-data`   export `app/data/venues.json` for the map (commit it after any seed change; CI runs `ci/check_export_fresh.py`); `make app` serves it at localhost:8765
- `make extract` / `make load`   refresh raw data (extract takes ~15 min; don't run unless asked)
- `make check-links` / `make check-websites`   verify link-outs / flag dead venue sites
- `make issues`     read-only check of open GitHub issues (missing info, already in seeds, duplicates, waiting); runbook step 2b
- `make report`     regenerate `docs/coverage_snapshot.md`
- `make snowflake-build`   RETIRED (2026-10-14): do not run; DuckDB is the only warehouse

## Rules
- NEVER read, print or commit `.env` (credentials). `.env.example` shows the keys.
- Never hand-edit `transform/seeds/all_racquet.csv` or Snowflake `RAW.ALL_RACQUET`: the Google Sheet is the source, `make sync-sports` overwrites them.
  The sheet must stay in sync with the project: run `make sync-sports` at every project sync (twice a month, `docs/monthly_refresh.md` step 2) and carry renames/new sports through seeds, scripts and the app.
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
Full session log (2026-10-10 .. 10-15): `docs/status_history.md`. Plan: `~/.claude/plans/create-a-revised-plan-temporal-yao.md`. Add one short dated line per session here; keep the 3 newest session lines here and move the rest to the history file.

**Working practices**
- Build: `.venv/Scripts/dbt build --project-dir transform --profiles-dir transform` (no `make` in Git Bash). A worktree needs a copy of `courtconnect.duckdb`.
- Seed column changes need `--full-refresh`. **Snowflake is retired as of 2026-10-14 (access may be gone): DuckDB only, never build or sync Snowflake.** Its code stays until an ADR removes it.
- Commit `app/data/venues.json` after `make app-data`. Re-run `pages.yml` after merging any app/export change; check the latest run (another session's run cancels yours). Confirm a PR is MERGED before calling it shipped.
- Dirty main checkout: `git worktree add ../x -b branch origin/main`, use the main `.venv`, copy `.env` only for the Snowflake build, then delete it.

**Done (summary):** CA map with link-outs, confirmation levels, leads, suggest-a-change form -> PR workflow (ADR 0008), social/WhatsApp/Meetup/Partiful link-outs (ADR 0009/0010/0012), OSM edit link (ADR 0011), GoatCounter analytics (ADR 0013, site `courts`), logo C, UX Option A PRs 1-3, 43 tournament events, 265 hitting walls (LA/SD/Bay OSM + 2 owner), private-club passes 1-2 (partial), `ref_sport_fit`, `mart_sport_evidence`, `mart_venue_confidence` rules_v2 (not exported), `make quality` scorecard incl. 35-day freshness SLA, monthly runbook, ADR 0014 CalNeva step 1 (`REGIONS` in `ingestion/overpass.py`, `ci/check_regions.py`).

**Open, in order**
1. CalNeva (ADR 0014): steps 2-4 done (525 NV venues live). First NV seeds done (8 venues, 1 event). Next: more NV link-outs (Reno/Henderson parks, Life Time, Sun City Summerlin), NV manual venues if any; repo/Pages rename to `courtconnect` after the beta, target 2026-12-01, TBD (keep a redirect stub for the old Pages URL).
2. Beta round (docs/feedback_round.md): replies due 10-28, findings 10-29..11-01, then fill case study + docs/feedback_findings.md (RICE). Owner: exclude own IP in GoatCounter.
3. Visual polish (Option A PRs 1-4 live, `docs/ux_polish.md`): PAUSED until beta findings (10-29..11-01). Then optional B parts: PR 5 popup grouping + status band, PR 6 sport glyph pins. Owner to eyeball live at 375/320px + dark (never rendered by me: browser pane refuses localhost).
4. Accuracy: (band counts done 10-14j) Overture/OSM match gold set, clear the review queue from public pages (205 left after batch 4; pick batches from `docs/review_priority.csv`).
5. Small: owner to confirm Basque Pelota (Chino trinquet, South SF center) by 2026-11-16; owner review of UX live.
5b. Gym chain + public-facility courts, CA + NV (plans `docs/gym_chain_scan.md`, `docs/public_facility_scan.md`): LA Fitness, Bay Club, 24 Hour Fitness, ClubSport Aliso Viejo, Henderson + Las Vegas + Hawthorne public facilities done; Life Time/Equinox/Sports Club LA list no racquetball. The 4 leads are closed (2026-10-15). YMCA pass done (East Bay, SF, Silicon Valley, San Diego, Southern Nevada). Next (optional): other Y associations (Reno/Truckee Meadows, LA, Orange County, Sacramento), university and military rec centers, more city pages by region.
5c. Public facilities (city/county/park rec centers, all racket sports, CA + NV): plan in `docs/public_facility_scan.md`, pilot Hawthorne Sports Center (lead `hawthorne-sports-center`). Branch `public-facility-scan`.
5d. ML, plan in `docs/ml_plan.md`: phase 1 review-queue ranker BUILT (`make rank-review` -> `docs/review_priority.csv`; use it to pick review batches); after beta (from 11-02): phase 2 LLM reads public pages (ADR first), phase 3 pilot detecting courts in NAIP aerial photos (Hawthorne, then one LV zip; new courts go to OSM).
6. Coverage: `*-access` leads, ~440 club-named venues (pass 2 parked), beach tennis court locations from clubs, statewide walls (parked), NorCal Equinox, OSM fix list (optional).
7. Recheck: Club Locker (squash), Cosm events, badminton 2027 ORCs (Nov-Dec). From ~2026-11-02: split watch events into on-site vs virtual (screenings such as Cosm showing tennis): new `watch_format` value `screening` (column exists; add accepted_values test), app popup label/filter "On-site" / "Screening (shown on screen, not played here)", then add Cosm events as screenings. Plan: `~/.claude/plans/i-wonder-if-we-dazzling-frog.md`.
8. LATER (after beta): optional read-only CourtConnect MCP server over `venues.json` (details in docs/status_history.md, TODO 2026-10-14; ADR first).

**Sessions**
- 2026-10-15k: YMCA of Superior California (Sacramento; 6 fitness branches, pickleball page + branch amenity lists): pickleball at Rollingwood, Sacramento Central, Yolo County; tennis at Rollingwood; racquetball at Capital. Rollingwood merged onto the pin at its own address (was 'JMG Tennis Academy', the Y's tennis program): correct. Gold Country, Oroville: no courts.
- 2026-10-15l: YMCA of Orange County (7 fitness branches, ymcaoc.org): no racquetball/tennis/squash; pickleball at Laguna Niguel (gym schedule PDF), Fullerton (2025 schedule, Basketball Gym), Huntington Beach, Mission Viejo, Newport-Mesa (Active Older Adults lists it; setting/counts unknown). South Coast Metro, Rancho Mission Viejo none. No merges.
- 2026-10-15m: planned on-site vs virtual watch events (Cosm screenings) as open item 7, start ~2026-11-02. Docs only.
