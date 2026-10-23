-- One row per hitting wall: hand-curated (seeds/manual_walls.csv) plus those mapped in OpenStreetMap. Blank flags stay NULL
-- (unknown); `confirmation` says how we know (reported / official by hand, tagged = from OSM tags only).
-- A hand-added one-wall / three-wall court (a report or official page says what it is) beats the OSM default for the same court:
-- OSM walls within `wall_group_radius_m` of one are dropped, so the confirmed pin is the only one shown. Backboards and
-- other types don't hide OSM walls (a backboard is a different structure from a handball court nearby).
select * from {{ ref('stg_manual_walls') }}
union all
select o.*
from {{ ref('stg_osm_walls') }} o
where not exists (
    select 1
    from {{ ref('stg_manual_walls') }} m
    where m.wall_type in ('one_wall', 'three_wall', 'one_wall;three_wall')
      and abs(m.lat - o.lat) < 0.01
      and sqrt(
              power((m.lat - o.lat) * 110540, 2)
            + power((m.lon - o.lon) * cos(radians(m.lat)) * 111320, 2)
          ) <= {{ var('wall_group_radius_m') }}
)
