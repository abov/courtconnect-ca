-- GoatCounter page views and events per day (ADR 0013). Counts only, no visitors.
-- Source: docs/usage_daily.csv, written by `make usage` (ingestion/usage_daily.py) and committed, so CI and fresh worktrees have it with no token.
-- The path is relative to where dbt runs (the repo root, like the DuckDB file in profiles.yml).
select
    cast("day" as date)         as day,
    cast("page_views" as int)   as page_views,
    cast("events" as int)       as events
from read_csv('docs/usage_daily.csv', header = true, all_varchar = true)
