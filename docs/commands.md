# Commands

Moved out of `CLAUDE.md` on 2026-11-17 so every session does not load it (token efficiency). `CLAUDE.md` keeps the five commands used most. Run from Git Bash on Windows (no `make` there: run the script behind the target, see the `Makefile`).

- `make build`      dbt seeds + models + tests (the main check; run after any change to `transform/`)
- `make build-changed`   only what changed since the last good build, plus downstream (`ingestion/build_changed.py`; no `make` in Git Bash: run the script; `--full` or `--dry-run`). Use it for seed, model, macro and test edits. After loading raw data (new state, refresh) it cannot see the change: run `--full`. It skips Elementary's dashboard uploads (~25s; tests still run; `--elementary` keeps them). CI and the last check before a PR are the plain full `dbt build`.
- `make app-data`   export `app/data/venues.json` for the map (commit it after any seed change; CI runs `ci/check_export_fresh.py`); `make app` serves it at localhost:8765
- `make hub`   regenerate `app/hub.html` (the short project hub) and `app/all-docs.html` (every doc and tool) from `docs/README.md` and `docs/all_docs.md`; run after editing either, CI (`ci/check_docs_hub.py`) fails when it is stale
- `make extract` / `make load`   refresh raw data (extract takes ~15 min; don't run unless asked)
- `make push-data`   after extract + load: dry-run list of what differs from the private data repo `abov/courtconnect-data`; `ARGS=--push` commits and pushes it (`ingestion/push_data_bundle.py`; refuses files that shrank >10% unless `--force`)
- `make check-links` / `make check-websites`   verify link-outs / flag dead venue sites
- `make check-pages`   list verified pages that changed or vanished since the last look (conditional requests + text hash, no model); recheck only those
- `make sync-reports`   import owner-approved community-form reports as seed edits (needs `REPORTS_CSV_URL` in `.env`; `ARGS=--dry-run` previews)
- `make issues`     read-only check of open GitHub issues (missing info, already in seeds, duplicates, waiting); runbook step 2b
- `make feedback`   sync every GitHub issue (open and closed) into `docs/feedback_log.csv`, list what is open/handled and any comment after close; log non-issue feedback with `ARGS="--add --channel message --reporter <tag> --summary ..."` (no emails/phones; commit the CSV)
- `make usage`      export GoatCounter counts and print the usage metrics + sport demand vs coverage (needs `GOATCOUNTER_API_TOKEN` in `.env`; `docs/goat_analysis.md`)
- `make interest`   Google Trends search interest vs venues per metro (planning signal, `docs/search_interest_plan.md`)
- `make ask-feedback`   after `make usage`: load the ask-box questions visitors chose to send (unanswered ones) into the local warehouse (`mart_ask_feedback`; never commit the text; `docs/goat_analysis.md`)
- `make report`     regenerate `docs/coverage_snapshot.md`
- `make ops-metrics`   merged PRs/day, conflict-commit signal, CI/Pages/dbt durations, Claude token use (`docs/ops_metrics.md`; needs `gh`)
- `make observability`   Elementary data-observability report from the local warehouse (`docs/data_observability.md`; `make build` records the history and installs the package)
