-- Fails if an OSM wall pin still stands within `wall_group_radius_m` of a hand-added one-wall / three-wall court: the confirmed
-- court should be the only pin (see dim_wall).
select o.wall_key
from {{ ref('dim_wall') }} o
join {{ ref('dim_wall') }} m
    on m.wall_key not like 'osm-%'
   and m.wall_type in ('one_wall', 'three_wall', 'one_wall;three_wall')
   and abs(m.lat - o.lat) < 0.01
   and sqrt(
           power((m.lat - o.lat) * 110540, 2)
         + power((m.lon - o.lon) * cos(radians(m.lat)) * 111320, 2)
       ) <= {{ var('wall_group_radius_m') }}
where o.wall_key like 'osm-%'
