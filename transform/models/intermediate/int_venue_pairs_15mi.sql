-- Helper for the market marts: every (venue, sport at ANOTHER venue) pair within 15 miles, straight-line (not drive time).
-- Only sports a venue is directly listed for count: sports that exist only as an "also played" inference (sport_also_played, e.g. Frescotennis
-- on every tennis court) would inflate every number, so they are left out here.
with vs as (
    select distinct venue_id, sport_name, lat, lon
    from {{ ref('mart_venue_finder') }}
    where lat is not null
      and lon is not null
      and sport_name not in (select trim(also_sport) from {{ ref('sport_also_played') }})
),

venues as (
    select venue_id, any_value(lat) as lat, any_value(lon) as lon
    from vs
    group by 1
)

select
    a.venue_id,
    b.venue_id  as other_venue_id,
    b.sport_name,
    {{ distance_mi('a.lat', 'a.lon', 'b.lat', 'b.lon') }}  as dist_mi
from venues a
join vs b
  on b.venue_id <> a.venue_id
 and abs(b.lat - a.lat) < 0.22      -- 15 miles is ~0.217 degrees of latitude: cheap prefilter before the exact distance
 and abs(b.lon - a.lon) < 0.30      -- ~0.28 degrees of longitude at 40N
where {{ distance_mi('a.lat', 'a.lon', 'b.lat', 'b.lon') }} <= 15
