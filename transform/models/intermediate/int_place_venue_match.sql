-- Link each Overture place to the OSM venue it is part of: the nearest OSM court/facility within
-- `place_match_radius_m` metres. Same grid-bucket trick as int_court_pairs, so it scales statewide.
{% set radius = var('place_match_radius_m') %}
{% set cell = radius / 80000.0 %}

with places as (
    select place_id, lat, lon,
           cast(floor(lat / {{ cell }}) as bigint) as cy,
           cast(floor(lon / {{ cell }}) as bigint) as cx
    from {{ ref('stg_overture_places') }}
),

courts as (
    select c.court_id, c.lat, c.lon, md5(k.cluster_label) as venue_id,
           cast(floor(c.lat / {{ cell }}) as bigint) as cy,
           cast(floor(c.lon / {{ cell }}) as bigint) as cx
    from {{ ref('stg_osm_courts') }} c
    join {{ ref('int_court_clusters') }} k on k.court_id = c.court_id
),

offsets as (
    select -1 as d union all select 0 union all select 1
),

candidates as (
    select
        p.place_id, c.venue_id,
        sqrt(power((p.lat - c.lat) * 110540, 2)
           + power((p.lon - c.lon) * cos(radians(p.lat)) * 111320, 2)) as distance_m
    from places p
    cross join offsets dy
    cross join offsets dx
    join courts c on c.cy = p.cy + dy.d and c.cx = p.cx + dx.d
)

select place_id, venue_id, distance_m
from (
    select *, row_number() over (partition by place_id order by distance_m, venue_id) as rn
    from candidates
    where distance_m <= {{ radius }}
) x
where rn = 1
