-- One row per hitting wall: hand-curated (seeds/manual_walls.csv) plus those mapped in OpenStreetMap. Blank flags stay NULL
-- (unknown); `confirmation` says how we know (reported / official by hand, tagged = from OSM tags only).
select * from {{ ref('stg_manual_walls') }}
union all
select * from {{ ref('stg_osm_walls') }}
