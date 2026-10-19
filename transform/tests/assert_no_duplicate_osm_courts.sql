-- Fails (returns rows) if two OSM pitch ways of the same sport sit within osm_court_duplicate_radius_m of each other:
-- stg_osm_courts should have kept only the lower id, otherwise the venue's court count is inflated.
select a.court_id as kept, b.court_id as duplicate
from {{ ref('stg_osm_courts') }} a
join {{ ref('stg_osm_courts') }} b
    on a.court_id < b.court_id
   and a.osm_leisure_type = 'pitch' and b.osm_leisure_type = 'pitch'
   and a.sport_tag_delimited = b.sport_tag_delimited
   and abs(a.lat - b.lat) < 0.0001
where sqrt(
          power((a.lat - b.lat) * 110540, 2)
        + power((a.lon - b.lon) * cos(radians(a.lat)) * 111320, 2)
      ) <= {{ var('osm_court_duplicate_radius_m') }}
