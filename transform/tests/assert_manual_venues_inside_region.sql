-- A hand-entered venue with a mistyped coordinate (swapped lat/lon, missing minus sign) or a missing/wrong region must fail the build.
select venue_key, lat, lon, region
from {{ ref('stg_manual_venues') }}
where {{ outside_region_bbox('lat', 'lon', 'region') }}
