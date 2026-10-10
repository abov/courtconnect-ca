-- A hand-added venue is often a place we already hold under another source (a park whose courts are in OpenStreetMap,
-- a club Overture lists). Link it to the nearest such venue within `manual_match_radius_m` metres so the map shows ONE pin,
-- enriched by the hand-added details, instead of two. Otherwise it stays a venue of its own.
{% set radius = var('manual_match_radius_m') %}
{% set cell = radius / 80000.0 %}

with manual as (
    select distinct
        venue_key, venue_id as own_venue_id, lat, lon,
        cast(floor(lat / {{ cell }}) as bigint) as cy,
        cast(floor(lon / {{ cell }}) as bigint) as cx
    from {{ ref('stg_manual_venues') }}
),

known as (
    select md5(k.cluster_label) as venue_id, c.lat, c.lon, 'osm' as matched_source,
           cast(floor(c.lat / {{ cell }}) as bigint) as cy, cast(floor(c.lon / {{ cell }}) as bigint) as cx
    from {{ ref('stg_osm_courts') }} c
    join {{ ref('int_court_clusters') }} k on k.court_id = c.court_id
    union all
    select p.venue_id, p.lat, p.lon, 'places',
           cast(floor(p.lat / {{ cell }}) as bigint), cast(floor(p.lon / {{ cell }}) as bigint)
    from {{ ref('dim_place') }} p
    where p.has_strong_sport
),

offsets as (
    select -1 as d union all select 0 union all select 1
),

candidates as (
    select
        m.venue_key, m.own_venue_id, k.venue_id as matched_venue_id, k.matched_source,
        sqrt(power((m.lat - k.lat) * 110540, 2) + power((m.lon - k.lon) * cos(radians(m.lat)) * 111320, 2)) as distance_m
    from manual m
    cross join offsets dy
    cross join offsets dx
    join known k on k.cy = m.cy + dy.d and k.cx = m.cx + dx.d
),

nearest as (
    select venue_key, matched_venue_id, matched_source, distance_m
    from (
        select *, row_number() over (partition by venue_key order by distance_m, matched_venue_id) as rn
        from candidates
        where distance_m <= {{ radius }}
    ) x
    where rn = 1
)

select
    m.venue_key,
    m.own_venue_id,
    coalesce(n.matched_venue_id, m.own_venue_id)              as effective_venue_id,
    n.matched_venue_id is not null                            as is_matched,
    n.matched_source,
    n.distance_m
from manual m
left join nearest n on n.venue_key = m.venue_key
