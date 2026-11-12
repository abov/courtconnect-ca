-- GoatCounter event counts per day, event name and detail (ADR 0013, docs/goat_analysis.md). Fixed vocabularies only; no typed text.
-- Source: docs/usage_events.csv, written by `make usage` (ingestion/usage_daily.py) and committed. Path relative to the repo root, where dbt runs.
select
    cast("day" as date)                  as day,
    "event"                              as event,
    coalesce(nullif(trim("detail"), ''), '') as detail,
    cast("count" as int)                 as event_count
from read_csv('docs/usage_events.csv', header = true, all_varchar = true)
