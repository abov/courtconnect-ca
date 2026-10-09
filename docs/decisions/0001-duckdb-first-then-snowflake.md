# ADR 0001: Develop on DuckDB, deploy to Snowflake

**Status:** accepted

## Context
Fast iteration and zero cloud cost matter during development, but the production target is Snowflake.

## Decision
dbt models are written once against two targets. Differences are isolated in `transform/macros/cross_db.sql`
(`adapter.dispatch`). `dbt build` runs locally on DuckDB in about a second; `--target snowflake` runs the same project in the cloud.

## Consequences
+ Tight feedback loop; CI is free and has no credentials.
+ Forces portable SQL.
- A few Snowflake-only features (dynamic tables, `GEOGRAPHY`, masking policies) can't be exercised locally and are tested only on the Snowflake target.
