-- A hand-entered venue with a mistyped coordinate (swapped lat/lon, missing minus sign) must fail the build.
select venue_key, lat, lon
from {{ ref('stg_manual_venues') }}
where lat is null or lon is null
   or lat not between 32.5 and 42.1
   or lon not between -124.5 and -114.1
