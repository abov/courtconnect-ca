-- Every pair of courts within `venue_radius_m` metres of each other (both directions), plus pairs of courts inside the
-- same named school/park/club/golf club that are within `parent_merge_radius_m` (a school's courts a few hundred
-- metres apart are one facility, not several). Matched on the lower-cased name, not the OSM id, because one school
-- or club is often mapped as several polygons.
-- Scales to a whole state: courts are bucketed into a grid whose cell is about one radius wide, and each court
-- is only compared with courts in its own and the 8 neighbouring cells (an equi-join, not a cross join).
{% set radius = var('venue_radius_m') %}
{% set cell = radius / 80000.0 %}

with cells as (
    select
        court_id, lat, lon,
        cast(floor(lat / {{ cell }}) as bigint) as cy,
        cast(floor(lon / {{ cell }}) as bigint) as cx
    from {{ ref('stg_osm_courts') }}
),

offsets as (
    select -1 as d union all select 0 union all select 1
)

select
    a.court_id as court_a,
    b.court_id as court_b
from cells a
cross join offsets dy
cross join offsets dx
join cells b
    on b.cy = a.cy + dy.d
   and b.cx = a.cx + dx.d
   and b.court_id <> a.court_id
where sqrt(
          power((a.lat - b.lat) * 110540, 2)
        + power((a.lon - b.lon) * cos(radians(a.lat)) * 111320, 2)
      ) <= {{ radius }}

union

select
    a.court_id as court_a,
    b.court_id as court_b
from {{ ref('int_court_parent') }} pa
join {{ ref('int_court_parent') }} pb
    on lower(pb.parent_name) = lower(pa.parent_name)
   and pb.court_id <> pa.court_id
join {{ ref('stg_osm_courts') }} a on a.court_id = pa.court_id
join {{ ref('stg_osm_courts') }} b on b.court_id = pb.court_id
where sqrt(
          power((a.lat - b.lat) * 110540, 2)
        + power((a.lon - b.lon) * cos(radians(a.lat)) * 111320, 2)
      ) <= {{ var('parent_merge_radius_m') }}
