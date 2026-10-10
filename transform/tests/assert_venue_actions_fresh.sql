{{ config(severity='warn') }}
-- Prices, dates and sign-up status on provider sites change. Warn when a CURRENT link-out has not been re-checked for 60 days.
select action_key, verified_on
from {{ ref('stg_venue_actions') }}
where (end_date is null or end_date >= current_date)
  and verified_on < current_date - 60
