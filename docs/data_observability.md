# Data observability (Elementary, added 2026-11-02)

Free, open source, local: the [Elementary](https://docs.elementary-data.com/) dbt package (`transform/packages.yml`, pinned 0.26.1) records every dbt run and test result in the `elementary` schema of `courtconnect.duckdb`, and adds anomaly tests. No account, no cloud, no spend. Anonymous usage tracking of its CLI is off (`transform/edr_config/config.yml`). It stores run history, test results and row counts only, no venue rows.

## What it watches (warn-only, tag `observability`, never blocks a build)
- `dim_court` and `mart_venue_finder` (the table behind the map): row-count anomalies and a per-`region` count anomaly (a state suddenly gaining or losing venues). `mart_venue_finder` also gets a `schema_changes` test (a column added, dropped or retyped).
- Add more by putting `elementary.volume_anomalies` / `dimension_anomalies` / `schema_changes` under a model's `tests:` in `transform/models/schema.yml`.

## See it
```bash
make build            # installs the package (dbt deps), builds, runs the tests, records history
make observability    # writes observability/elementary_report.html (git-ignored); open it in a browser
```
One-time setup for the report: the CLI pins its own dbt, so it lives in `.venv-edr` next to the main `.venv` (a short path matters on Windows: inside a deep worktree path its own packages exceed the 260-character limit):
```bash
python -m venv /c/dev/courtconnect-ca/.venv-edr && /c/dev/courtconnect-ca/.venv-edr/Scripts/pip install "elementary-data[duckdb]" "duckdb<2"
```

## Limits (be honest about them)
- **Anomaly tests need history.** They pass with "not enough data" until about 3 days with a run exist, so on the first runs they prove nothing. History lives only in the `courtconnect.duckdb` you keep running `make build` against (the main checkout's, at each twice-monthly sync). CI and Pages build a fresh database from fixtures each time, so Elementary never learns anything there; the tests are there harmlessly. A fresh worktree database starts with no history too.
- With one run per sync, the 3-bucket minimum arms after about three syncs. Lower `min_training_set_size` or run `make build` more often to arm sooner.
- It does not check the raw extracts; `ingestion/load_raw.py` (shrink guard) and `make quality` (freshness SLA) still do that.
- It does not replace the Evidence.dev dashboard (`dashboard/`): that shows the product scorecard, this shows pipeline health.
