# CourtConnect CalNeva

Racket-sport venue finder for California + Nevada ("CalNeva", ADR 0014): Python ingestion -> dbt (DuckDB dev/CI, Snowflake prod) -> static MapLibre map in `app/`.
README.md has the full story; read it only if you need background. Mission (ADR 0015): help people find every place to play or watch racket sports in CA + NV, discover sports beyond pickleball (tennis stays visible), and get together to play.
Decisions are in `docs/decisions/` (ADRs 0001-0018, all accepted; one file each, read only the one you need).

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
- Never put the owner's email or any personal contact in request headers, query strings or forms sent to outside services (geocoders, APIs, scrapers). Identify requests with the project contact only: `User-Agent: courtconnect-ca/0.1 (+https://github.com/abov/courtconnect-ca)`.
- Never hand-edit `transform/seeds/all_racquet.csv` or Snowflake `RAW.ALL_RACQUET`: the Google Sheet is the source, `make sync-sports` overwrites them.
  The sheet must stay in sync with the project: run `make sync-sports` at every project sync (twice a month, `docs/monthly_refresh.md` step 2) and carry renames/new sports through seeds, scripts and the app.
- Data edits go in seeds, then `make build`:
  - `manual_venues.csv` (venues no dataset knows), `venue_actions.csv` (link-outs; keep `verified_on` + `evidence`),
  - `watch_events.csv` (https links only), `place_sport_overrides.csv` (confirm/reject uncertain matches), `sport_aliases.csv`, `closed_places.csv` (Overture places that no longer exist but are still listed open; `place_id` + `evidence` + `verified_on`).
- DuckDB only (ADR 0018): new SQL needs no Snowflake-safe form; keep the existing `adapter.dispatch` macros, don't add engine-specific SQL without need.
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
- One task per session. Keep sessions small: when context passes ~200-300k tokens, write the session note and tell me to start a fresh session.
- At the end of a session, write a 2-3 line note in a NEW file `docs/sessions/YYYY-MM-DD-<topic>.md` (what changed, what is next). Never edit another session's note or add lines to a shared log: that is what caused merge conflicts. Update "Open, in order" below only when priorities change.
- Use a lighter model for simple edits; save the biggest for hard problems.

## Where things are
- `ingestion/`   Python extract/load/export scripts
- `transform/`   dbt project (models, seeds, macros, tests)
- `app/`         static map page
- `ci/fixtures`  small sample data for CI

## Current status
Session notes: one file per session in `docs/sessions/` (read only the newest 1-2 when picking up). Older log: `docs/status_history.md`. Plan: `~/.claude/plans/create-a-revised-plan-temporal-yao.md`.

**Working practices**
- Build: `.venv/Scripts/dbt build --project-dir transform --profiles-dir transform` (no `make` in Git Bash). A new worktree has no `courtconnect.duckdb`: run `python ingestion/fresh_db.py` (`make fresh-db`; ~1 min, loads the shared raw CSVs and runs the full dbt build) instead of copying one. Raw CSVs live in ONE shared folder, the main checkout's `data/raw` (`ingestion/rawdir.py`; override with `COURTCONNECT_DATA_DIR`): extract/load scripts from any worktree read and write it, and `load_raw.py` refuses to shrink a table by more than 10% unless `--force`.
- Seed column changes need `--full-refresh`. **Snowflake is retired as of 2026-10-14 (access may be gone): DuckDB only, never build or sync Snowflake.** Its code stays dormant until the post-beta removal PR (ADR 0018).
- Commit `app/data/venues.json` after `make app-data`. Re-run `pages.yml` after merging any app/export change; check the latest run (another session's run cancels yours). Confirm a PR is MERGED before calling it shipped.
- Before starting a task: `git fetch`, check `git log origin/main --since=1.day --oneline` and `gh pr list`, and skim the newest `docs/sessions/` notes, so you don't redo work another session already landed (2026-10-17: city fill and the Padel guard-rail test were each built twice).
- Avoid merge conflicts: sync with main (rebase or merge) right before opening and again before merging a PR. `app/data/venues.json` is generated and any two PRs that touch it collide: never hand-resolve it; take main's copy, rebuild (`dbt build --full-refresh`), re-run `make app-data`, commit.
- Dirty main checkout: `git worktree add ../x -b branch origin/main`, use the main `.venv`, copy `.env` only for the Snowflake build, then delete it.

**Done (summary):** CA map with link-outs, confirmation levels, leads, suggest-a-change form -> PR workflow (ADR 0008), social/WhatsApp/Meetup/Partiful link-outs (ADR 0009/0010/0012), OSM edit link (ADR 0011), GoatCounter analytics (ADR 0013, site `courts`), logo C, UX Option A PRs 1-3, 43 tournament events, 265 hitting walls (LA/SD/Bay OSM + 2 owner), private-club passes 1-2 (partial), `ref_sport_fit`, `mart_sport_evidence`, `mart_venue_confidence` rules_v2 (not exported), `make quality` scorecard incl. 35-day freshness SLA, address fill tiers 1-3 + city fill (2026-10-17), mode buttons renamed "Play" / "Watch" (2026-10-17), monthly runbook, ADR 0014 CalNeva step 1 (`REGIONS` in `ingestion/overpass.py`, `ci/check_regions.py`).

**Open, in order** (detail per item, dated results and numbers: `docs/roadmap_history.md`; old numbers there are in brackets)

*Doable now* (priority order; one task per session)
1. CalNeva (ADR 0014): steps 2-4 done, 525 NV venues live; NV park seeds done. Resort gyms CLOSED by the owner 2026-10-17: do not re-check NV resorts/casinos. Next: repo/Pages rename to `courtconnect` after the beta (date TBD; keep a redirect stub for the old Pages URL).
2. Street addresses (tiers 1-3, 1b and "Near <street>" built; `int_venue_address`, `docs/ml_plan.md`): after every extract rerun `ingestion/reverse_geocode_blanks.py` (+ `dbt build`, `make app-data`) and `extract_osm_parents.py` after each OSM refresh; city fill is DONE (2026-10-17): every pin has a city (last 59 from Census place / county boundaries, `ingestion/place_from_boundaries.py` -> `venue_place_boundary.csv`; `make city-boundaries` after an extract that leaves new cityless pins; boundaries are the reference table `raw.census_boundaries`, `make extract-boundaries`). Home-like pins never get an inferred street (owner 2026-10-16); OSM-tagged ones are kept. Tier 4 (official page + quote in `manual_venues.csv`) needs the phase 2 reader.
3. Backboards / 1-wall courts (was 1b): `manual_walls.csv` rows need `confirmation` + `evidence` + `reported_on`; walls use the venue access vocabulary (#212). LA, SD, Bay Area, Sacramento, OC, Fresno, IE city pages checked: more metros one at a time, only if cheap. Statewide walls parked.
4. Padel leads (was 1c, `docs/padel_scan.md`): audit, directory sweep, guard-rail test and "Opening soon" pins are done. In December, or sooner if the owner reports an opening, recheck the 3 light "Reported" pins (Ballers DTLA, King of Padel at West Harbor, WynPadel at the Westin Rancho Mirage: promote by setting their `venue_opening_status.csv` value to `Opening soon` once an official page confirms) and the other coming-soon clubs in `venue_leads.csv`; when a club opens, delete its status row and update the venue (courts, address, access).
5. Match gold set (was 4, `docs/gold_set_plan.md`): 90 labels (`make eval-match`); `facility_name` match rule added 2026-10-17 (0 wrong merges, 30 duplicate pins gone); next: a second random sample incl. places 300 m+ from courts.
6. Facility scans (was 5b/5c, `docs/gym_chain_scan.md`, `docs/public_facility_scan.md`): optional next: City of San Diego rec centers, Sacramento area, Orange County, Inland Empire, other UC/CSU campuses, more military MWR.
7. Coverage (was 6): `*-access` leads (48 unresolved), club-named venues pass 2, beach tennis court locations, NorCal Equinox, OSM fix list.
8. Rechecks (was 7): Club Locker (squash), badminton 2027 ORCs (Nov-Dec), Cosm events (add only after the screening split below).

*After beta (December; rank with beta findings, ADR 0015)*
- Beta round (was 9, `docs/feedback_round.md`; dates TBD): send, collect, record findings (RICE, `docs/feedback_findings.md`). Owner: exclude own IP in GoatCounter.
- Visual polish (was 3, `docs/ux_polish.md`): PR 5 popup grouping + status band, PR 6 sport glyph pins; owner eyeballs 375/320px + dark. Phone view (found 2026-10-17, `docs/sessions/2026-10-17-ring-visual-check.md`): the legend is hidden below 800 px so the Opening soon / Reported rings are explained only by the popup caveat, and the popup is tall and scrolls inside the 341 px phone map: add a short ring key on phones and make the popup fit.
- Tennis visibility + sport discovery (was 7b): own pin look, never hidden in a pickleball pin, "Try something new" card.
- All 76 sheet sports in the dropdown + "About <sport>" card (was 7b2, `docs/sport_discovery_plan.md`).
- Watch events split on-site vs `screening` (was 7): `watch_format` value + accepted_values test + popup label, then Cosm events.
- Social phase A, "Find people to play with" (was 7c, `docs/competitor_scan.md`); phase B only with its own ADR.
- Player-connection platforms (added 2026-10-17): consider integrating with, or building a format like, https://connectplayers.ca/ and similar player-matching platforms. Scan them first (public pages only, add to `docs/competitor_scan.md`), then decide link-out vs. own format; own accounts/matching = phase B, own ADR.
- Cost tier "Free / $ / $$ / $$$" (was 7f): ADR first, labelled inferred unless confirmed on a public page, members-only gets no tier.
- ML phases 2-3 (was 5d, `docs/ml_plan.md`): LLM page reader (ADR 0017, accepted 2026-10-17) and NAIP aerial pilot (Hawthorne, then one LV zip; new courts go to OSM).
- ITF 2027 calendars (was 7e, ~Dec): facts only (name, dates, venue, link), no scraping; read ITF pages singly in the browser pane.
- Optional read-only MCP server over `venues.json` (was 8; ADR first).

*Parked / waiting on owner*
- City of Sparks parks and `cityofsparks.us`: never retry unless the owner asks. NV resort/casino courts: closed, do not re-check.
- Review queue (parked 2026-10-17, 116 rows left; `docs/review_priority.csv` for reference): needs the phase 2 reader or community reports; the ~35 live-site rows pass is NOT planned.
- Community reports step 3, report without GitHub (was 7d): owner creates the Google Form first (`docs/community_reports_plan.md`).
- Owner to confirm Basque Pelota (Chino trinquet, South SF center) by 2026-11-16.
- Owner/community visit reports to confirm walls (Sacramento, Berkeley campus walls need an access label) (Pop Tennis pins Exeter, Garside and Kahler Russell were resolved by owner reports and imagery, 2026-10-17).
