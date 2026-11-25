# RacketConnect

Racket-sport venue finder for California, Nevada, Oregon, Washington, Arizona, New Mexico, Texas and Hawaii, plus a Mexico pilot (ADR 0014, 0028; region list: `ingestion/regions.json`): Python ingestion -> dbt (DuckDB, the only warehouse) -> static MapLibre map in `app/`. Product name RacketConnect (ADR 0029); the repo, DB file, dbt project and env vars keep the `courtconnect` names.
README.md has the full story; read it only if you need background. Mission (ADR 0015): one map for every racket sport in every region covered: find a court, watch a match, try a new sport, and find people to play with. Long-term goal: run itself with as little human review as possible, AI agents doing the work behind automated gates (see `docs/status.md`).
Decisions are in `docs/decisions/` (ADRs 0001-0040, all accepted except 0001, superseded by 0018, 0023 deferred, and 0024-0026, 0032 and 0036, proposed; one file each, read only the one you need).

## Commands (run from Git Bash on Windows; full list with every `make` target: `docs/commands.md`)
- `make build`      dbt seeds + models + tests (the main check; run after any change to `transform/`)
- `make build-changed`   only what changed since the last good build, plus downstream (`ingestion/build_changed.py`; no `make` in Git Bash: run the script; `--full` or `--dry-run`). For seed, model, macro and test edits. After loading raw data it cannot see the change: run `--full`. CI and the last check before a PR are the full build.
- `make app-data`   export `app/data/venues.json` (commit it after any seed change; CI runs `ci/check_export_fresh.py`) and its uncommitted split `map.json` + `details.json`, which the map loads; `make app` serves it at localhost:8765
- `make extract` / `make load`   refresh raw data (extract ~15 min; don't run unless asked)
- `make check-pages`   verified pages that changed or vanished since the last look (no model); recheck only those

## Rules
- NEVER read, print or commit `.env` (credentials; a hook blocks it). `.env.example` shows the keys.
- Never put the owner's email or any personal contact in request headers, query strings or forms sent to outside services (geocoders, APIs, scrapers). Identify requests with the project contact only: `User-Agent: courtconnect-ca/0.1 (+https://github.com/abov/courtconnect-ca)`.
- Never hand-edit `transform/seeds/all_racquet.csv`: the Google Sheet is the source, `make sync-sports` overwrites it.
  The sheet must stay in sync with the project: run `make sync-sports` at every project sync (twice a month, `docs/monthly_refresh.md` step 2) and carry renames/new sports through seeds, scripts and the app.
- Data edits go in seeds, then `make build`:
  - `manual_venues.csv` (venues no dataset knows), `venue_actions.csv` (link-outs; keep `verified_on` + `evidence`),
  - `watch_events.csv` (https links only), `place_sport_overrides.csv` (confirm/reject uncertain matches), `sport_aliases.csv`, `closed_places.csv` (Overture places that no longer exist but are still listed open; `place_id` + `evidence` + `verified_on`), `venue_court_counts.csv` (a person's court count for one sport at a venue where OSM's is wrong; `venue_id` + pin `lat`/`lon` + `evidence` + `verified_on`).
- DuckDB only (ADR 0018): new SQL needs no Snowflake-safe form; keep the existing `adapter.dispatch` macros, don't add engine-specific SQL without need.
- Courts not open yet (any sport, any region): when a venue's own page or an official page says courts are coming, still pin it: `manual_venues.csv` + a `venue_opening_status.csv` row (hollow pin, "Opening soon"; press/directory-only = "Reported: opening soon" + `venue_leads.csv`). Courts being added at a venue that already exists: keep the pin, put "Planned: N <sport> courts, source, date" in its `rules`. Delete the row / planned note when it opens; the 90-day staleness warning (`assert_opening_status_fresh`) flags old rows.
- Honesty over polish: label inferred data as inferred, never present guesses as confirmed. RacketConnect links out; it takes no bookings or payments.
- One rule for every region (owner 2026-11-12, ADR 0034): automatic pins show labelled inferred, including unnamed home-like ones (no inferred street); hide nothing by region or home-likeness without the owner's explicit ruling.
- NEVER use the owner's logins (Playtomic, PlayByPoint, Padel Up, etc.) or read logged-in pages; use public pages and what the owner reports (ADR 0007).
- Don't use Google Places data (terms forbid storing it); Overture + OSM only (ADR 0005). The Google place-ID layer (`stg_google_place_ids.sql`, `ingestion/google_place_ids.py`) stays dormant (owner 2026-10-22, "for now"): don't delete it, don't run it.
- No partnership or data-license emails (Pickleheads, USA Pickleball/Places2Play, other court apps) until the owner is ready to socialize or monetize (2026-10-16); their data is off limits. Sources are public pages and community reports.
- Operator is not venue (owner 2026-10-17): name a pin after the place where the courts are; put the operator (e.g. Taktika) in `rules` and its booking links in `venue_actions.csv`; never credit an operator at a place that does not list it. Where brand = place (Padel Up, Bay Padel), the brand location is the venue (`docs/padel_scan.md`, "Rules learned").
- Merging (owner 2026-11-16, every PR): the session itself merges once `dbt-build` is green; no "Ship it?" question. Squash, never bypass failing checks; `--admin` only when blocked solely by the review rule (no reviewers yet). Afterwards confirm MERGED, the Pages deploy (if `app/**` or the workflow changed) and the live site.
- Search results skip generated paths (`.rgignore`); don't open `transform/target`, `transform/logs`, `courtconnect.duckdb`, `app/data/venues.json` whole.

## Working practices (full text and reasons: `docs/working_practices.md`)
- Build: `.venv/Scripts/dbt build --project-dir transform --profiles-dir transform`. New worktree: `python ingestion/fresh_db.py` (~1 min), never copy a DB. Raw CSVs are shared in the main checkout's `data/raw`. Seed column changes need `--full-refresh`.
- Before a task: `git fetch`, `git log origin/main --since=1.day --oneline`, `gh pr list` (don't redo landed work).
- Before EVERY push: fetch, rebase onto `origin/main`, run build + `ci/check_export_fresh.py` + `ci/check_docs_hub.py`, fix, then push. Once per clone: `python ingestion/setup_git.py`.
- `venues.json` conflict: take main's copy, rebuild, `make app-data`, commit; never hand-resolve (`docs/merge_conflicts.md`).
- After extract: `ingestion/reverse_geocode_blanks.py` (+ build, `make app-data`); after an OSM refresh: `extract_osm_parents.py` and `make eval-match`. Home-like pins never get an inferred street.
- New region = full CA parity: `docs/new_region_checklist.md`, done only when `python ci/region_parity.py --region XX --strict` passes. No new-state sessions now (owner 2026-11-13); existing-state passes are fine.
- Priorities, dated detail, parked items: `docs/status.md` (edit it only when priorities change). Hand-off is the PR description and `git log`; only automated routines write `docs/sessions/` notes. Never add lines to a shared log. Older history: `docs/archive/session_digest.md`.
- Resorts and hotels with courts (all states, ADR 0028): case by case; add what non-guests can book with access stated, flag guests/members-only; Hawaii resorts: ask the owner first.
- Closed, don't redo: City of Sparks, the Google place-ID layer (dormant), NAIP aerial pilot, partnership emails. Basque Pelota only from public online sources.
- Project hub: `docs/README.md` is the one hub: three doors (use it, how it's built, run it), then every doc, page and tool under "All docs and tools". Add, rename or remove a doc there in the same task, then `make hub` (`ci/check_docs_hub.py`). Tool changes also update the tool dictionary row (link in `docs/tools_and_strategies.md`).
- Layout: `ingestion/` (extract/load/export; `oneoff/` = one-time scans, outside requests use `ingestion/useragent.py`), `transform/` (dbt), `app/` (static map), `chatbot/` (ask-box checks), `ci/` (checks; `ci/fixtures` = sample data).

## Keeping usage low (hooks enforce the first three: `docs/token_efficiency.md`)
- No browser screenshots and no image reads unless I ask; read pages as text (`get_page_text` / `read_page`). Read `app/index.html` only by line range. Prefer `WebFetch` with a specific question over dumping pages.
- Cheapest path that does the job, said in one line: Grep/Read/Edit directly; no subagents, deep-research or extended web search unless asked; narrowest check first (`build_changed.py`, `dbt build --select`), full build once at the end (required before opening or merging a PR, after raw loads, after seed column changes); batch tool calls; stop when done.
- Never start `make extract`/`make load`, or loops/scheduled tasks, without asking. If a task looks expensive (many pages, big refactor), propose the scoped version first.
- One task per session (research passes: one region or sport in one region). At ~150k context (a hook warns) finish the step, put the hand-off in the PR description and tell me to start fresh.
- Lighter model for simple edits; biggest only for hard problems.
- Short everywhere (owner 2026-10-22): replies lead with the result, at most ~5 bullets; recaps 1-2 sentences; PR descriptions 2-4 bullets; commits one line plus at most two. No tables unless asked.
