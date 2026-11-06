-- A venue the confidence mart marks with a closure signal must have no live Overture place and no live OSM court (ADR 0026): a lost single source only lowers the score.
select c.venue_id
from {{ ref('mart_venue_confidence') }} c
join (
    select venue_id, bool_or(in_places) as live_places, bool_or(in_osm) as live_osm
    from {{ ref('bridge_venue_sport') }}
    group by 1
) b on b.venue_id = c.venue_id
where c.closure_signal is not null and (b.live_places or b.live_osm)
