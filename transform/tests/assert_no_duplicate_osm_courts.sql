-- Fails (returns rows) if two OSM pitch ways of the same sport sit within osm_court_duplicate_radius_m of each other:
-- stg_osm_courts should have kept only the lower id, otherwise the venue's court count is inflated.
-- Pitches are bucketed by (sport tag, latitude cell of 0.0001 deg) and probed in the cell and its two neighbours, so
-- the join is an equi-join; the old `abs(a.lat - b.lat) < 0.0001` range join took ~110 s.
with pitches as (
    select court_id, lat, lon, sport_tag_delimited, cast(floor(lat / 0.0001) as bigint) as cy
    from {{ ref('stg_osm_courts') }}
    where osm_leisure_type = 'pitch'
),

probe as (
    select a.*, a.cy + d.d as ny
    from pitches a
    cross join (select -1 as d union all select 0 union all select 1) d
)

select a.court_id as kept, b.court_id as duplicate
from probe a
join pitches b
    on b.sport_tag_delimited = a.sport_tag_delimited
   and b.cy = a.ny
   and a.court_id < b.court_id
where abs(a.lat - b.lat) < 0.0001
  and sqrt(
          power((a.lat - b.lat) * 110540, 2)
        + power((a.lon - b.lon) * cos(radians(a.lat)) * 111320, 2)
      ) <= {{ var('osm_court_duplicate_radius_m') }}
