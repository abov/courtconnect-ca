-- Every pair of courts within `venue_radius_m` metres of each other (both directions).
-- A cheap lat/lon box filter runs first so the exact distance maths touches few rows.
{% set radius = var('venue_radius_m') %}
{% set box_deg = radius / 80000.0 %}

select
    a.court_id as court_a,
    b.court_id as court_b
from {{ ref('stg_osm_courts') }} a
join {{ ref('stg_osm_courts') }} b
    on a.court_id <> b.court_id
   and abs(a.lat - b.lat) < {{ box_deg }}
   and abs(a.lon - b.lon) < {{ box_deg }}
where sqrt(
          power((a.lat - b.lat) * 110540, 2)
        + power((a.lon - b.lon) * cos(radians(a.lat)) * 111320, 2)
      ) <= {{ radius }}
