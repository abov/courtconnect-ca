-- One row per venue (ADR 0032): court facilities (int_venue_court: OSM courts grouped by proximity, Overture places, hand-added rows;
-- venue_kind 'courts') plus the hitting walls that stand at no listed venue (int_wall_venue; venue_kind 'hitting_wall', venue_source 'walls').
-- Walls at a listed venue add their sports to it instead (bridge_venue_sport.in_wall). sport_count includes the wall sports.
select
    u.* exclude (sport_count),
    coalesce(s.sport_count, 0) as sport_count
from (
    select * from {{ ref('int_venue_court') }}
    union all by name
    select * from {{ ref('int_wall_venue') }}
) u
left join (
    select venue_id, count(distinct sport_id) as sport_count
    from {{ ref('bridge_venue_sport') }}
    group by 1
) s on s.venue_id = u.venue_id
