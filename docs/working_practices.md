# Working practices

Moved out of `CLAUDE.md` on 2026-11-17 (token efficiency: `CLAUDE.md` is re-read every turn; this file is read when needed). `CLAUDE.md` keeps a short version of each rule; this is the full text. Priorities and dated detail are in [`status.md`](status.md).

## Build and databases
- Build: `.venv/Scripts/dbt build --project-dir transform --profiles-dir transform` (no `make` in Git Bash; run `dbt deps` with the same flags once per checkout first, it installs Elementary, `docs/data_observability.md`). A new worktree has no `courtconnect.duckdb`: run `python ingestion/fresh_db.py` (`make fresh-db`; ~1 min, loads the shared raw CSVs and runs the full dbt build) instead of copying one. Raw CSVs live in ONE shared folder, the main checkout's `data/raw` (`ingestion/rawdir.py`; override with `COURTCONNECT_DATA_DIR`): extract/load scripts from any worktree read and write it, and `load_raw.py` refuses to shrink a table by more than 10% unless `--force`.
- Seed column changes need `--full-refresh`. Snowflake was retired 2026-10-14 and its code removed 2026-10-21 (ADR 0018): DuckDB only.
- Dirty main checkout: `git worktree add ../x -b branch origin/main`, use the main `.venv`.

## Shipping
- Commit `app/data/venues.json` after `make app-data`. `pages.yml` deploys by itself when a merge to main touches `app/**` (or the workflow); check the latest run after merging (a newer run cancels an older one). `gh workflow run pages.yml` still runs it by hand. Confirm a PR is MERGED before calling it shipped.
- Before starting a task: `git fetch`, check `git log origin/main --since=1.day --oneline` and `gh pr list`, so you don't redo work another session already landed (2026-10-17: city fill and the Padel guard-rail test were each built twice).
- Before EVERY push (owner 2026-11-12): `git fetch`, rebase onto `origin/main`, run the local CI checks (build, `ci/check_export_fresh.py`, `ci/check_docs_hub.py`), fix what fails, then push. `.githooks/pre-push` enforces the cheap part (enable: `git config core.hooksPath .githooks`).
- Avoid merge conflicts (`docs/merge_conflicts.md`): run `python ingestion/setup_git.py` once per clone (rerere + venues.json merge driver). Sync with main (rebase or merge) right before opening and again before merging a PR. `app/data/venues.json` is generated, one venue per line: the driver merges it and rebuilds its meta line; after any merge still rebuild (`dbt build`), re-run `make app-data` and `ci/check_export_fresh.py`. On a real conflict take main's copy, rebuild, re-export, commit; never hand-resolve it. Append-only logs and seeds merge with `union` (`.gitattributes`): a duplicate row after a merge shows up as a unique-test failure; delete the stale one.

## Standing rules after data work
- Street addresses: after every extract run `ingestion/reverse_geocode_blanks.py` (+ build, `make app-data`); run `extract_osm_parents.py` after each OSM refresh. Home-like pins never get an inferred street.
- Match gold set: re-run `make eval-match` after each OSM refresh.
- Padel lead rechecks run in Part 3 of the cloud routines (`docs/cloud_routines.md`); facility scans and coverage leads are in `docs/status.md`.
- New states and countries get full CA parity (walls, handball, events, social, leads): follow `docs/new_region_checklist.md` and do not call a region done until `python ci/region_parity.py --region XX --strict` passes (owner 2026-11-03; Arizona shipped as data layer only). Research passes: one region (or one sport in one region) per session.

## Token-saving enforcement
Rules that used to be prose in `CLAUDE.md` are enforced by `.claude/hooks/guard.py` (wired in `.claude/settings.json`): it blocks reading `.env` and the bulky generated files, asks before reading images or taking browser screenshots, and warns when a session gets long. `.rgignore` keeps search results out of generated files. See [`token_efficiency.md`](token_efficiency.md).
