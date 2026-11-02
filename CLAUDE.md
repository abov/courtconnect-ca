# RacketConnect

Racket-sport venue finder for California + Nevada (ADR 0014, 0028): Python ingestion -> dbt (DuckDB, the only warehouse) -> static MapLibre map in `app/`. Product name RacketConnect (ADR 0029); the repo, DB file, dbt project and env vars keep the `courtconnect` names.
README.md has the full story; read it only if you need background. Mission (ADR 0015): one map for every racket sport in CA + NV: find a court, watch a match, try a new sport, and find people to play with. Long-term goal: run itself with as little human review as possible, AI agents doing the work behind automated gates (see `docs/status.md`).
Decisions are in `docs/decisions/` (ADRs 0001-0027, all accepted except 0001, superseded by 0018, and 0023-0026, proposed; one file each, read only the one you need).

## Commands (run from Git Bash on Windows)
- `make build`      dbt seeds + models + tests (the main check; run after any change to `transform/`)
- `make app-data`   export `app/data/venues.json` for the map (commit it after any seed change; CI runs `ci/check_export_fresh.py`); `make app` serves it at localhost:8765
- `make extract` / `make load`   refresh raw data (extract takes ~15 min; don't run unless asked)
- `make check-links` / `make check-websites`   verify link-outs / flag dead venue sites
- `make sync-reports`   import owner-approved community-form reports as seed edits (needs `REPORTS_CSV_URL` in `.env`; `ARGS=--dry-run` previews)
- `make issues`     read-only check of open GitHub issues (missing info, already in seeds, duplicates, waiting); runbook step 2b
- `make usage`      export GoatCounter counts and print the usage metrics + sport demand vs coverage (needs `GOATCOUNTER_API_TOKEN` in `.env`; `docs/goat_analysis.md`)
- `make interest`   Google Trends search interest vs venues per metro (planning signal, `docs/search_interest_plan.md`)
- `make report`     regenerate `docs/coverage_snapshot.md`
- `make observability`   Elementary data-observability report from the local warehouse (`docs/data_observability.md`; `make build` records the history and installs the package)

## Rules
- NEVER read, print or commit `.env` (credentials). `.env.example` shows the keys.
- Never put the owner's email or any personal contact in request headers, query strings or forms sent to outside services (geocoders, APIs, scrapers). Identify requests with the project contact only: `User-Agent: courtconnect-ca/0.1 (+https://github.com/abov/courtconnect-ca)`.
- Never hand-edit `transform/seeds/all_racquet.csv`: the Google Sheet is the source, `make sync-sports` overwrites it.
  The sheet must stay in sync with the project: run `make sync-sports` at every project sync (twice a month, `docs/monthly_refresh.md` step 2) and carry renames/new sports through seeds, scripts and the app.
- Data edits go in seeds, then `make build`:
  - `manual_venues.csv` (venues no dataset knows), `venue_actions.csv` (link-outs; keep `verified_on` + `evidence`),
  - `watch_events.csv` (https links only), `place_sport_overrides.csv` (confirm/reject uncertain matches), `sport_aliases.csv`, `closed_places.csv` (Overture places that no longer exist but are still listed open; `place_id` + `evidence` + `verified_on`), `venue_court_counts.csv` (a person's court count for one sport at a venue where OSM's is wrong; `venue_id` + pin `lat`/`lon` + `evidence` + `verified_on`).
- DuckDB only (ADR 0018): new SQL needs no Snowflake-safe form; keep the existing `adapter.dispatch` macros, don't add engine-specific SQL without need.
- Honesty over polish: label inferred data as inferred, never present guesses as confirmed. RacketConnect links out; it takes no bookings or payments.
- NEVER use the owner's logins (Playtomic, PlayByPoint, Padel Up, etc.) or read logged-in pages; use public pages and what the owner reports (ADR 0007).
- Don't use Google Places data (terms forbid storing it); Overture + OSM only (ADR 0005). The Google place-ID layer (`stg_google_place_ids.sql`, `ingestion/google_place_ids.py`) stays dormant (owner 2026-10-22, "for now"): don't delete it, don't run it.
- No partnership or data-license emails (Pickleheads, USA Pickleball/Places2Play, other court apps) until the owner is ready to socialize or monetize (2026-10-16); their data is off limits. Sources are public pages and community reports.
- Operator is not venue (owner 2026-10-17): name a pin after the place where the courts are; put the operator (e.g. Taktika) in `rules` and its booking links in `venue_actions.csv`; never credit an operator at a place that does not list it. Where brand = place (Padel Up, Bay Padel), the brand location is the venue (`docs/padel_scan.md`, "Rules learned").
- Merging: only after `dbt-build` is green and the owner says "ship it" in chat; that means merge, confirm the Pages deploy, check the live site. Use `gh pr merge <n> --squash --admin` only when blocked solely by the review rule (no reviewers yet); never bypass failing checks. An agent-opened PR still needs that explicit yes.
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
- One task per session. Keep sessions small: when context passes ~200-300k tokens, tell me to start a fresh session.
- No session note for ordinary work: put what changed and what is next in the PR description. Only the automated routines write `docs/sessions/` notes (their handshake, see `docs/sessions/README.md`). Never add lines to a shared log (that caused merge conflicts). Update `docs/status.md` only when priorities change.
- Use a lighter model for simple edits; save the biggest for hard problems.
- Keep summaries short everywhere (owner 2026-10-22): chat replies lead with the result and use at most ~5 bullets, wrap-up recaps are 1-2 sentences, PR descriptions 2-4 bullets, commit messages one line plus at most two. No tables or per-feature breakdowns unless asked; offer detail instead.

## Where things are
- `ingestion/`   Python extract/load/export scripts (`ingestion/oneoff/`: one-time research scans, not in any make target; outside requests use `ingestion/useragent.py`)
- `transform/`   dbt project (models, seeds, macros, tests)
- `app/`         static map page
- `ci/fixtures`  small sample data for CI

## Current status
Hand-off is the PR description and `git log`; `docs/sessions/` holds only the routines' notes. Older history and past decisions: `docs/archive/session_digest.md`. Plan: `~/.claude/plans/create-a-revised-plan-temporal-yao.md`.

**Working practices**
- Build: `.venv/Scripts/dbt build --project-dir transform --profiles-dir transform` (no `make` in Git Bash; run `dbt deps` with the same flags once per checkout first, it installs Elementary, `docs/data_observability.md`). A new worktree has no `courtconnect.duckdb`: run `python ingestion/fresh_db.py` (`make fresh-db`; ~1 min, loads the shared raw CSVs and runs the full dbt build) instead of copying one. Raw CSVs live in ONE shared folder, the main checkout's `data/raw` (`ingestion/rawdir.py`; override with `COURTCONNECT_DATA_DIR`): extract/load scripts from any worktree read and write it, and `load_raw.py` refuses to shrink a table by more than 10% unless `--force`.
- Seed column changes need `--full-refresh`. Snowflake was retired 2026-10-14 and its code removed 2026-10-21 (ADR 0018): DuckDB only.
- Commit `app/data/venues.json` after `make app-data`. `pages.yml` deploys by itself when a merge to main touches `app/**` (or the workflow); check the latest run after merging (a newer run cancels an older one). `gh workflow run pages.yml` still runs it by hand. Confirm a PR is MERGED before calling it shipped.
- Before starting a task: `git fetch`, check `git log origin/main --since=1.day --oneline` and `gh pr list`, so you don't redo work another session already landed (2026-10-17: city fill and the Padel guard-rail test were each built twice).
- Avoid merge conflicts: sync with main (rebase or merge) right before opening and again before merging a PR. `app/data/venues.json` is generated and any two PRs that touch it collide: never hand-resolve it; take main's copy, rebuild (`dbt build --full-refresh`), re-run `make app-data`, commit.
- Dirty main checkout: `git worktree add ../x -b branch origin/main`, use the main `.venv`.

**Priorities** (dated detail for every item, the "After beta" list and the parked items: `docs/status.md`; edit it there when priorities change)
1. Five states (ADR 0028/0029): Oregon and Washington data layers are built; their events, leagues and groups passes are done (`docs/event_group_search.md`); rec centers, chains and campuses are not; then Hawaii. New states get full CA parity (walls, handball, events, social, leads).
2. Street addresses: after every extract run `ingestion/reverse_geocode_blanks.py` (+ build, `make app-data`); run `extract_osm_parents.py` after each OSM refresh. Home-like pins never get an inferred street.
3. Match gold set: re-run `make eval-match` after each OSM refresh.
4. Padel lead rechecks run in Part 3 of the cloud routines (`docs/cloud_routines.md`); facility scans and coverage leads are in `docs/status.md`.
5. After the December beta: polish, player finding, sport suggestions, favorites email, ML phases, monetization (`docs/status.md`).

**Closed, don't redo:** NV resorts/casinos, City of Sparks, the Google place-ID layer (dormant), NAIP aerial pilot (dropped), partnership emails. Basque Pelota only from public online sources.
