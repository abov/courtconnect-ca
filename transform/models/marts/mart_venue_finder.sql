-- What the app queries: one row per (venue, sport) with the facts a player cares about:
-- how many courts, which surfaces (hard / clay / grass / sand / ...), indoor and/or outdoor.
select
    v.venue_id,
    coalesce(v.venue_name, 'Unnamed courts')                  as venue_name,
    v.name_source,
    s.sport_name,
    count(distinct case when c.record_kind = 'court' then c.court_id end) as courts_for_sport,
    v.lat,
    v.lon,
    v.city,
    v.address_line,
    v.website,
    v.phone,
    v.opening_hours,
    max(case when c.setting = 'indoor' then 1 else 0 end) = 1                   as has_indoor,
    max(case when c.setting in ('outdoor', 'likely_outdoor', 'covered') then 1 else 0 end) = 1 as has_outdoor,
    max(case when c.surface_type = 'sand' then 1 else 0 end) = 1                as has_sand_beach,
    max(case when c.surface_type = 'clay' then 1 else 0 end) = 1                as has_clay,
    max(case when c.surface_type = 'grass' then 1 else 0 end) = 1               as has_grass,
    max(case when c.surface_type = 'hard' then 1 else 0 end) = 1                as has_hard,
    max(case when c.surface_type = 'turf' then 1 else 0 end) = 1                as has_turf,
    v.has_lit_courts,
    v.is_confirmed_public,
    v.has_free_courts
from {{ ref('dim_venue') }} v
join {{ ref('dim_court') }} c on c.venue_id = v.venue_id
join {{ ref('bridge_court_sport') }} b on b.court_id = c.court_id
join {{ ref('dim_sport') }} s on s.sport_id = b.sport_id
group by v.venue_id, v.venue_name, v.name_source, s.sport_name, v.lat, v.lon, v.city, v.address_line,
         v.website, v.phone, v.opening_hours, v.has_lit_courts, v.is_confirmed_public, v.has_free_courts
