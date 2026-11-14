{{ config(severity='warn') }}
-- "Opening soon" goes stale: clubs open, slip or vanish. Warn when a row has not been re-checked for 90 days (delete it if the venue opened).
select venue_key, opening_status, verified_on
from {{ ref('venue_opening_status') }}
where cast(verified_on as date) < current_date - 90
