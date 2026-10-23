# CourtConnect CalNeva

Racket-sport venue finder for California + Nevada ("CalNeva", ADR 0014): Python ingestion -> dbt (DuckDB, the only warehouse) -> static MapLibre map in `app/`.
README.md has the full story; read it only if you need background. Mission (ADR 0015): one map for every racket sport in CA + NV: find a court, watch a match, try a new sport, and find people to play with. Long-term goal: run itself with as little human review as possible, AI agents doing the work behind automated gates (see "After beta").
Decisions are in `docs/decisions/` (ADRs 0001-0021, all accepted except 0001, superseded by 0018; one file each, read only the one you need).

## Commands (run from Git Bash on Windows)
- `make build`      dbt seeds + models + tests (the main check; run after any change to `transform/`)
- `make app-data`   export `app/data/venues.json` for the map (commit it after any seed change; CI runs `ci/check_export_fresh.py`); `make app` serves it at localhost:8765
- `make extract` / `make load`   refresh raw data (extract takes ~15 min; don't run unless asked)
- `make check-links` / `make check-websites`   verify link-outs / flag dead venue sites
- `make sync-reports`   import owner-approved community-form reports as seed edits (needs `REPORTS_CSV_URL` in `.env`; `ARGS=--dry-run` previews)
- `make issues`     read-only check of open GitHub issues (missing info, already in seeds, duplicates, waiting); runbook step 2b
- `make report`     regenerate `docs/coverage_snapshot.md`

## Rules
- NEVER read, print or commit `.env` (credentials). `.env.example` shows the keys.
- Never put the owner's email or any personal contact in request headers, query strings or forms sent to outside services (geocoders, APIs, scrapers). Identify requests with the project contact only: `User-Agent: courtconnect-ca/0.1 (+https://github.com/abov/courtconnect-ca)`.
- Never hand-edit `transform/seeds/all_racquet.csv`: the Google Sheet is the source, `make sync-sports` overwrites it.
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
  - Never start `make extract`/`make load`, or loops/scheduled tasks, without asking.
  - Prefer one batched tool call over many; stop once the task is done instead of extra "nice to have" work.
  - If a task looks expensive (many pages to research, big refactor), propose the cheaper scoped version first and wait for my OK.
- Read only the lines you need from big files; don't dump whole CSVs, logs or `venues.json`.
- One task per session. Keep sessions small: when context passes ~200-300k tokens, write the session note and tell me to start a fresh session.
- At the end of a session, write a 2-3 line note in a NEW file `docs/sessions/YYYY-MM-DD-<topic>.md` (what changed, what is next). Never edit another session's note or add lines to a shared log: that is what caused merge conflicts. Update "Open, in order" below only when priorities change.
- Use a lighter model for simple edits; save the biggest for hard problems.
- Keep summaries short everywhere (owner 2026-10-22): chat replies lead with the result and use at most ~5 bullets, wrap-up recaps are 1-2 sentences, PR descriptions 2-4 bullets, commit messages one line plus at most two. No tables or per-feature breakdowns unless asked; offer detail instead.

## Where things are
- `ingestion/`   Python extract/load/export scripts (`ingestion/oneoff/`: one-time research scans, not in any make target; outside requests use `ingestion/useragent.py`)
- `transform/`   dbt project (models, seeds, macros, tests)
- `app/`         static map page
- `ci/fixtures`  small sample data for CI

## Current status
Session notes: one file per session in `docs/sessions/` (read only the newest 1-2 when picking up). Older log: `docs/archive/status_history.md`. Plan: `~/.claude/plans/create-a-revised-plan-temporal-yao.md`.

**Working practices**
- Build: `.venv/Scripts/dbt build --project-dir transform --profiles-dir transform` (no `make` in Git Bash). A new worktree has no `courtconnect.duckdb`: run `python ingestion/fresh_db.py` (`make fresh-db`; ~1 min, loads the shared raw CSVs and runs the full dbt build) instead of copying one. Raw CSVs live in ONE shared folder, the main checkout's `data/raw` (`ingestion/rawdir.py`; override with `COURTCONNECT_DATA_DIR`): extract/load scripts from any worktree read and write it, and `load_raw.py` refuses to shrink a table by more than 10% unless `--force`.
- Seed column changes need `--full-refresh`. Snowflake was retired 2026-10-14 and its code removed 2026-10-21 (ADR 0018): DuckDB only.
- Commit `app/data/venues.json` after `make app-data`. `pages.yml` deploys by itself when a merge to main touches `app/**` (or the workflow); check the latest run after merging (a newer run cancels an older one). `gh workflow run pages.yml` still runs it by hand. Confirm a PR is MERGED before calling it shipped.
- Before starting a task: `git fetch`, check `git log origin/main --since=1.day --oneline` and `gh pr list`, and skim the newest `docs/sessions/` notes, so you don't redo work another session already landed (2026-10-17: city fill and the Padel guard-rail test were each built twice).
- Avoid merge conflicts: sync with main (rebase or merge) right before opening and again before merging a PR. `app/data/venues.json` is generated and any two PRs that touch it collide: never hand-resolve it; take main's copy, rebuild (`dbt build --full-refresh`), re-run `make app-data`, commit.
- Dirty main checkout: `git worktree add ../x -b branch origin/main`, use the main `.venv`.

**Done (summary):** CA map with link-outs, confirmation levels, leads, suggest-a-change form -> PR workflow (ADR 0008), social/WhatsApp/Meetup/Partiful link-outs (ADR 0009/0010/0012), OSM edit link (ADR 0011), GoatCounter analytics (ADR 0013, site `courts`), logo C, UX Option A PRs 1-3, 43 tournament events, 265 hitting walls (LA/SD/Bay OSM + 2 owner), private-club passes 1-2 (partial), `ref_sport_fit`, `mart_sport_evidence`, `mart_venue_confidence` rules_v2 (not exported), `make quality` scorecard incl. 35-day freshness SLA, address fill tiers 1-3 + city fill (2026-10-17), mode buttons renamed "Play" / "Watch" (2026-10-17), monthly runbook, ADR 0014 CalNeva step 1 (`REGIONS` in `ingestion/overpass.py`, `ci/check_regions.py`).

**Open, in order** (detail per item, dated results and numbers: `docs/archive/roadmap_history.md`; old numbers there are in brackets)

*Doable now* (priority order; one task per session)
1. CalNeva (ADR 0014): steps 2-4 done, 525 NV venues live; NV park seeds done. Resort gyms CLOSED by the owner 2026-10-17: do not re-check NV resorts/casinos. Next: repo/Pages rename to `courtconnect` after the beta (date TBD; keep a redirect stub for the old Pages URL).
2. Street addresses (tiers 1-3, 1b and "Near <street>" built; `int_venue_address`, `docs/ml_plan.md`): after every extract rerun `ingestion/reverse_geocode_blanks.py` (+ `dbt build`, `make app-data`) and `extract_osm_parents.py` after each OSM refresh; city fill is DONE (2026-10-17): every pin has a city (last 59 from Census place / county boundaries, `ingestion/place_from_boundaries.py` -> `venue_place_boundary.csv`; `make city-boundaries` after an extract that leaves new cityless pins; boundaries are the reference table `raw.census_boundaries`, `make extract-boundaries`). Home-like pins never get an inferred street (owner 2026-10-16); OSM-tagged ones are kept. Tier 4 (official page + quote in `manual_venues.csv`) needs the phase 2 reader.
3. Padel leads (was 1c, `docs/padel_scan.md`): audit, directory sweep, guard-rail test and "Opening soon" pins are done. Lead rechecks (the 3 light "Reported" pins and the coming-soon clubs in `venue_leads.csv`) now run in the scheduled `courtconnect-tournament-refresh` task, step 2c (owner 2026-10-21): it opens a PR, nothing to remember here. Still open: the "padel = walled glass court, pop tennis = open court with a low net" blurb in the Google Sheet (owner; the About card is built and shows it once the sheet has it, the suggest-a-change form has it already); the OSM tag fixes (`docs/padel_scan.md` step 6) are optional.
4. Match gold set (was 4, `docs/gold_set_plan.md`): 90 labels (`make eval-match`); `facility_name` rule 2026-10-17, radius 300 m + city-name guard and a second random sample (121 pairs, 0 wrong merges, 11 missed) 2026-10-18; `inside_facility` footprint tier 2026-10-18 (129 pairs, 0 wrong, 4 missed; `docs/gold_set_plan.md`, "Fourth slice"); next: re-run `make eval-match` after each OSM refresh; only worth a new rule if the beta shows the 4 remaining misses matter.
5. Facility scans (was 5b/5c, `docs/gym_chain_scan.md`, `docs/public_facility_scan.md`): City of San Diego rec centers (#311), Sacramento area (#312), Inland Empire (#314) and Orange County (#315) done 2026-10-21. Optional next: Cordova RPD and Cosumnes CSD (JS lists, need the browser pane), Folsom (403), Roseville (pages not found), other UC/CSU campuses, more military MWR.
6. Coverage (was 6): `*-access` leads (37 open after #309 resolved 10, 2026-10-21; the Walnut Creek RC pin sits on an office address, consider removing it), club-named venues pass 2, beach tennis court locations, NorCal Equinox, OSM fix list.
7. Rechecks (was 7): Reno Pickleball series and Carson City Dinks & Drinks (no 2027 dates yet, 2026-10-21; Toys for Tots pin moved to Desert Vista CC, #313); 3WallBall (3wallball.com, Outdoor Racquetball): Vegas World Championships has no 2027 dates yet (last held 2024), recheck each sync and add it when dates post; Huntington Beach Nationals is in (July 9-11, 2027); Club Locker (squash), badminton 2027 ORCs (Nov-Dec), Cosm events (add only after the screening split below).

*After beta (December; rank with beta findings, ADR 0015)*
- Beta round (was 9, `docs/feedback_round.md`; dates TBD): send, collect, record findings (RICE, `docs/feedback_findings.md`). Owner: exclude own IP in GoatCounter.
- Visual polish (was 3, `docs/ux_polish.md`): PR 5 popup grouping + status band, PR 6 sport glyph pins; owner eyeballs 375/320px + dark. Phone view: ring key and bottom-sheet popup done 2026-10-21; plain-language popup + filter labels done the same day.
- Watch events split on-site vs `screening` (was 7): `watch_format` value + accepted_values test + popup label, then Cosm events.
- Social / open-source next step (phase B, own ADR): social phase A is CLOSED (owner 2026-10-21; built: Watch & Social view, `social_events.csv`, `player_platforms.csv`; `player_groups.csv` keeps filling via scheduled step 2d but no shelf is planned). Anything further (own format like https://connectplayers.ca/, own accounts/matching) needs a new idea and its own ADR first.
- Cost tier "Free / $ / $$ / $$$" (was 7f): ADR first, labelled inferred unless confirmed on a public page, members-only gets no tier.
- ML + agents strategy (added 2026-10-21, umbrella plan `docs/ml_strategy.md`: tracks, agent roster, scoreboard, phased roadmap; Phase 0 needs only the owner's OK, no spend).
- ML phases 2-3 (was 5d, `docs/ml_plan.md`): LLM page reader (ADR 0017; `ingestion/page_reader.py` built, free `--engine rules` measured 2026-10-19, Claude-engine run waits on the owner's API key + spend cap + precision bar) and NAIP aerial pilot (Hawthorne and one LV zip run: LV recall 46%, not worth scaling without fine-tuning; new courts go to OSM).
- ITF 2027 calendars (was 7e, ~Dec): facts only (name, dates, venue, link), no scraping; read ITF pages singly in the browser pane.
- Optional read-only MCP server over `venues.json` (was 8; ADR first).
- Self-service goal (added 2026-10-18, ADR 0015): automated-first, minimal human review. A few scheduled agents (refresh, issue triage, link/closure watcher, page reader, lead rechecker) run observe -> propose (seed edit + evidence) -> verify -> merge. Automated gates (dbt tests, CI, freshness SLA, scorecard no-regression, diff cap, evidence required, second AI check) replace pre-approval; low-risk classes auto-merge when green, risky ones (closing venues on thin evidence, new sources, rule changes) escalate to the owner. Safety net: PR audit trail, easy revert, weekly AI-audited sample digest, kill switch, spend cap. Plan: `docs/self_service_plan.md` (steps classified mechanical / evidence / judgment). Rules for unattended merges: ADR 0019 (accepted 2026-10-18, stage 0 only): agents may open PRs, humans still merge; a class auto-merges only after it earns it and the owner switches it on; spend cap $20/month. Stage stuff done: classification, ADR 0019, scorecard + sport-name checks in CI. **Next (todo, later):** a draft-mode `refresh` agent that runs the runbook and opens the PR while a person merges (ADR 0019 stage 0). It needs a schedule, which needs the owner's go-ahead first (never start scheduled tasks unasked); until then run the runbook by hand.

*Parked / waiting on owner*
- Backboards / 1-wall courts (was 1b, then 3; `manual_walls.csv` rows need `confirmation` + `evidence` + `reported_on`, venue access vocabulary, #212): official city pages are exhausted (LA, SD, Bay Area, Sacramento, OC, Fresno, IE, Las Vegas + Clark County, Ventura, Reno, Santa Barbara; last checked 2026-10-21, only the SB Municipal Tennis Center walls, already seeded). New walls only from owner/community reports or imagery. Statewide walls parked.
- City of Sparks parks and `cityofsparks.us`: never retry unless the owner asks. NV resort/casino courts: closed, do not re-check.
- Review queue (parked 2026-10-17, 116 rows left; `docs/review_priority.csv` for reference): needs the phase 2 reader or community reports; the ~35 live-site rows pass is NOT planned.
- Community reports step 3 (was 7d) is BUILT (form live, popup link, `make sync-reports`); owner step: add `REPORTS_CSV_URL` to `.env`, then run it at each sync (runbook 2b). `docs/community_reports_plan.md`.
- Sport About card blurbs (was 7b2; dropdown with all 81 sheet sports DONE, #262/#301): owner pastes `docs/sport_details_draft.csv` (63 blurbs) into the sheet's Blurb/URL columns, then `make sync-sports` + `make app-data` (`docs/sport_discovery_plan.md`).
- Basque Pelota (Chino trinquet, South SF center): the owner will not confirm directly or in person (2026-10-18); confirm only from public online user sources (Yelp, Reddit, venue/club pages), evidence URL in the seed.
- Owner/community visit reports to confirm walls (Sacramento, Berkeley campus walls need an access label) (Pop Tennis pins Exeter, Garside and Kahler Russell were resolved by owner reports and imagery, 2026-10-17).
