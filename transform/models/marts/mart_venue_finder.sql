-- What the app should query: one row per (venue, sport) with the facts a player cares about.
select
    v.venue_id,
    coalesce(v.venue_name, 'Unnamed courts')                  as venue_name,
    s.sport_name,
    count(distinct c.court_id)                                as courts_for_sport,
    v.lat,
    v.lon,
    v.has_lit_courts,
    v.is_confirmed_public,
    v.has_free_courts,
    v.name_source
from {{ ref('dim_venue') }} v
join {{ ref('dim_court') }} c on c.venue_id = v.venue_id
join {{ ref('bridge_court_sport') }} b on b.court_id = c.court_id
join {{ ref('dim_sport') }} s on s.sport_id = b.sport_id
group by v.venue_id, v.venue_name, s.sport_name, v.lat, v.lon,
         v.has_lit_courts, v.is_confirmed_public, v.has_free_courts, v.name_source
