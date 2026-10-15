# CourtConnect CalNeva

Racket-sport venue finder for California + Nevada ("CalNeva", ADR 0014): Python ingestion -> dbt (DuckDB dev/CI, Snowflake prod) -> static MapLibre map in `app/`.
README.md has the full story; read it only if you need background. Decisions are in `docs/decisions/` (ADRs 0001-0014, all accepted; one file each, read only the one you need).

## Commands (run from Git Bash on Windows)
- `make build`      dbt seeds + models + tests (the main check; run after any change to `transform/`)
- `make app-data`   export `app/data/venues.json` for the map (commit it after any seed change; CI runs `ci/check_export_fresh.py`); `make app` serves it at localhost:8765
- `make extract` / `make load`   refresh raw data (extract takes ~15 min; don't run unless asked)
- `make check-links` / `make check-websites`   verify link-outs / flag dead venue sites
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
Full session log (2026-10-10 .. 10-14): `docs/status_history.md`. Plan: `~/.claude/plans/create-a-revised-plan-temporal-yao.md`. Add one short dated line per session here; move old lines to the history file when this passes ~15 lines.

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
4. Accuracy: (band counts done 10-14j) Overture/OSM match gold set, clear the review queue from public pages (247 left after batch 1; ~25 per session).
5. Small: owner to confirm Basque Pelota (Chino trinquet, South SF center) by 2026-11-16; owner review of UX live.
6. Coverage: `*-access` leads, ~440 club-named venues (pass 2 parked), beach tennis court locations from clubs, statewide walls (parked), NorCal Equinox, OSM fix list (optional).
7. Recheck: Club Locker (squash), Cosm events, badminton 2027 ORCs (Nov-Dec).
8. LATER (after beta): optional read-only CourtConnect MCP server over `venues.json` (details in docs/status_history.md, TODO 2026-10-14; ADR first).

**Sessions**
- 2026-10-14c: CalNeva step 2 merged (#67, Pages redeployed): `region` CA/NV through raw -> dims -> mart -> export `r`; Overture's address state is `address_region`; bbox tests are `assert_*_inside_region`. All 9,941 venues CA. A parallel duplicate (#70) was closed.
- 2026-10-14d: status log moved to docs/status_history.md (this section trimmed).
- 2026-10-14e: CalNeva step 3 (labels): app/README/CONTRIBUTING/case study/architecture/exposures say CalNeva; the app headline adds "California only so far; Nevada coming next" until any NV venue exists; watch-events coordinate test accepts CA or NV boxes; coverage snapshot (regenerated, was 10-10) lists venues by region. Historical docs (ADRs 0001-0013, outreach email, feedback invite, roadmap) left as is. Re-run pages.yml after merge.
- 2026-10-14f: Sunset Padel LA: `sunsetpadel.com` (Miami Beach club) flagged in `website_overrides`, lead resolved; map no longer links it. Snowflake not yet synced.
- 2026-10-14g: header mode buttons fit one line (PRs #73, #75 merged, Pages redeployed, checked live): phones (<=800px) show Play / Watch / Walls (full label as aria-label/title, 44px on touch, 375/320px); desktop shows full labels, content-sized + nowrap, 34px tall (was 55px). Pages caches up to 10 min (hard refresh if stale).
- 2026-10-14h: CalNeva step 4: statewide Nevada OSM extract into `data/raw/*_nv.csv` (`load_raw.py` appends them; `make extract` runs both states), Overture keeps CA+NV (same 2026-09-23.1 release). 525 NV venues on the map; CA unchanged at 9,941. DuckDB + Snowflake green. Re-run pages.yml after merge.
- 2026-10-14j: map sport dropdown counts now follow the location/filters (Padel (1) for "las vegas"; `sportCounts()` in app/index.html). Snowflake retired, DuckDB only; owner is new to DuckDB (explain access simply).
- 2026-10-14i: Nevada seeds: 28 link-outs on 8 NV venues (P1 Padel, Vegas Indoor Pickleball, Darling TC, Dill Dinkers Henderson, Pickleball Universe, Vegas Badminton Academy, Incline Village, Washoe TC) + PickleX K-Pop show (Darling, 2026-11-14) watch event; new providers in app `PROVIDER`; dropped unused `dim_sport.likely_in_california`. Leads: LV Badminton Club site says closed; 3rd Shot Reno page 404; vegasttc.com no DNS. Seeds must keep CRLF (mixed endings break DuckDB's sniffer). DuckDB + Snowflake green.
- 2026-10-14j: `make quality` shows confidence band counts (rules_v2, all/CA/NV via `dim_venue.region`; script only, not exported): high 75, medium 724, low 9,667. Next for item 3: Overture/OSM gold set, review queue.
- 2026-10-14k: review queue batch 1 (`mart_sport_evidence.needs_review`, was 272 not 249): 22 confirms + 3 rejects (equipment stores) from venues' own pages in `place_sport_overrides.csv` (new `evidence`, `verified_on` columns); queue 272 -> 247. Dead/unclear pages listed in the PR; places added to `ci/fixtures/overture_places.csv`. DuckDB only.
- 2026-10-14k: map count line follows the view (`updateCount()` in app/index.html): venues in view of filtered total + "at least N courts (M venues list a count)"; walls/events in view too. Counts data in bounds, not clusters; courts are only the ones listed.
- 2026-10-14l: sports sheet renamed 1-/4-wall Paddle to Paddleball and added 3-wall Paddleball (76 sports); synced + renamed through seeds/scripts/app. Hitting walls are no longer a mode: picking 1-wall or 3-wall Paddleball shows walls of known type (one-wall + backboards / three-wall) as orange pins; 261 unchecked-type walls stay out. Sheet must sync with the project at every twice-monthly sync (runbook step 2). Work is in worktree ../courtconnect-ca-paddleball (branch paddleball-sports, uncommitted). Another session stashed this work once (stash@{0}); same-checkout sessions collide.
- 2026-10-14m: visual polish scoped in `docs/ux_polish.md` (options A fresh court / B court-colour cards / C playful; recommend A then parts of B after beta). No code changed; waiting for owner's pick.
- 2026-10-14n: visual polish Option A shipped (#88 doc, #89 colour tokens, #90 shape/motion, #91 sport icons, #92 empty/loading + welcome line); CSS/JS only, no data change. Paused before B until beta findings.
- 2026-10-14o: NV link-outs small batch: only Whitney Mesa fits (City of Henderson tennis page, read in the browser pane; WebFetch gets 403 from cityofhenderson.com); Life Time Summerlin page states no guest/address, Sun City 403, Henderson rec-center directory 403 (leads stay). venue_actions can only link Overture places, not OSM-only parks: new lead `henderson-park-courts-city-table`. Provider `henderson_gov` added.
- 2026-10-14p: review queue batch 2 (Hub confirmed; crownvalleypickleball.org hijacked -> dead); sport dropdown has no counts; OSM handball/wallball walls = three_wall (262; 1-wall excludes them); Pop Tennis map now imports private clubs/apartments (5 added, access members/private), private homes never (importer fixed for `region`, CRLF); Venice Beach is Pop Tennis only (Tennis rejected at place + 11 OSM courts; `bridge_court_sport` no longer derives sports from a rejected tag); BracketSync draft deleted. DuckDB only.
