{{ config(severity='warn') }}
-- Event details go stale (dates move, tickets sell out). Warn when an UPCOMING event has not been re-checked for 120 days.
select event_key, verified_on
from {{ ref('stg_watch_events') }}
where (end_date is null or end_date >= current_date)
  and verified_on < current_date - 120
