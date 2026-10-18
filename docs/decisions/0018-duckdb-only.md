# 0018. DuckDB is the only warehouse (Snowflake retired)

Date: 2026-10-17. Status: accepted (records the 2026-10-14 retirement; amends ADR 0001).

## Context
ADR 0001 ("Develop on DuckDB, deploy to Snowflake") said every model runs unchanged on both engines. On 2026-10-14 Snowflake was retired (access may be gone) and CLAUDE.md started saying "DuckDB only, never build or sync Snowflake", but no ADR recorded it, so ADR 0001 still reads as current. Nothing has run on Snowflake since: CI is DuckDB only, the map reads `app/data/venues.json` exported from DuckDB, and the monthly refresh builds on DuckDB.

What Snowflake code still exists (grep, 2026-10-17):
- **Config and infra:** `transform/profiles.yml` (`snowflake` target), `infra/snowflake/00_setup.sql`, `.env.example` (`SNOWFLAKE_*` keys), `requirements.txt` (`dbt-snowflake`, `snowflake-connector-python`).
- **Scripts:** `Makefile` target `snowflake-build`; `ingestion/load_raw.py` (`--target snowflake`, `snowflake_connection`, `load_snowflake`).
- **Models:** `dim_venue.sql` has one `{% if target.type == 'snowflake' %}` block (a `GEOGRAPHY` column that no downstream model or the export reads). `cross_db.sql` has a `default__` and a `duckdb__` version of each macro and no `snowflake__` one, so the dispatch only separates DuckDB from "anything else". Other macros and comments (`website.sql`, `mart_venue_confidence.sql`) are written to be portable and mention Snowflake in comments only.
- **Workflows:** none. `ci.yml` and `pages.yml` never touch Snowflake.
- **Docs:** README, `docs/architecture.md` (+ svg), `docs/monthly_refresh.md` (two Snowflake steps), `docs/tournament_refresh.md`, ADRs 0003/0004/0005/0014 (history), `docs/status_history.md`, `docs/case_study.md`.
- **Sheet sync:** `make sync-sports` writes the Google Sheet into the seed `all_racquet.csv`. The Snowflake `RAW.ALL_RACQUET` copy was part of the retired build only.

## Decision
- **DuckDB is the only warehouse.** Dev, CI and the production export all use it. ADR 0001 is superseded for the deploy half; its "develop on DuckDB, keep SQL portable through `adapter.dispatch`" half stays as history.
- **(a) Removing the Snowflake code: allowed, but not in this change.** Nothing depends on it, so the removal is safe in principle, but it touches the Makefile, `load_raw.py`, `profiles.yml`, `requirements.txt` and a model, and it is easier to reverse if access ever returns while the code is still in git history than if it is kept half-working. The conservative path is: keep the code dormant for now, mark it retired (CLAUDE.md already does), and remove it in one follow-up PR after the December beta, with a dbt build on DuckDB to confirm nothing changed. The follow-up deletes: the `snowflake` profile output, `infra/snowflake/`, `snowflake-build`, the Snowflake branch of `load_raw.py`, the `target.type == 'snowflake'` block in `dim_venue.sql`, the two Snowflake packages, the `SNOWFLAKE_*` lines in `.env.example`, and the Snowflake steps in `docs/monthly_refresh.md`.
- **(b) The "run unchanged on DuckDB and Snowflake" rule: relaxed.** New models and macros no longer need a Snowflake-safe form. Keep using the existing `adapter.dispatch` macros where they exist (no churn), but plain DuckDB SQL is fine in new code, and nobody should run or test a Snowflake build to check it. The rule that still holds: do not make SQL needlessly engine-specific where a standard form is as easy.
- **No new Snowflake work:** no builds, no syncs, no `--target snowflake`, no new Snowflake-only code.

## Consequences
+ CLAUDE.md, README and ADR 0001 agree. New SQL can use DuckDB features (for example richer string, list and spatial functions) without a portability check.
+ One engine to test; "identical on both engines" claims in ADRs 0003, 0004 and 0005 stay true as history.
- If the project later needs a cloud warehouse, portability will have to be rebuilt and re-tested; that would need a new ADR.
- Until the follow-up PR lands, dead Snowflake code and `SNOWFLAKE_*` keys remain in the repo; they are not exercised and may rot.
