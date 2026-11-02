-- Which sports are played at which venue, and which source says so: the court sources (OSM, places, manual; int_venue_sport_courts)
-- plus hitting walls (in_wall, ADR 0032). A wall adds a sport to the venue it stands at; where a court source already lists the sport
-- the larger count wins (not the sum), like manual vs OSM.
select
    venue_id,
    sport_id,
    max(courts)        as courts,
    bool_or(in_osm)    as in_osm,
    bool_or(in_places) as in_places,
    bool_or(in_manual) as in_manual,
    bool_or(in_wall)   as in_wall
from (
    select venue_id, sport_id, courts, in_osm, in_places, in_manual, in_wall from {{ ref('int_venue_sport_courts') }}
    union all
    select venue_id, sport_id, courts, false, false, false, true from {{ ref('int_venue_sport_walls') }}
) u
group by 1, 2
