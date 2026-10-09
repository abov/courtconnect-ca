-- What the app queries: one row per (venue, sport) with the facts a player cares about:
-- how many courts, which surfaces (hard / clay / grass / sand / ...), indoor and/or outdoor, plus where the data came from.
with osm_facts as (
    select
        c.venue_id,
        b.sport_id,
        max(case when c.setting = 'indoor' then 1 else 0 end) = 1                                   as has_indoor,
        max(case when c.setting in ('outdoor', 'likely_outdoor', 'covered') then 1 else 0 end) = 1  as has_outdoor,
        max(case when c.surface_type = 'sand' then 1 else 0 end) = 1                                as has_sand_beach,
        max(case when c.surface_type = 'clay' then 1 else 0 end) = 1                                as has_clay,
        max(case when c.surface_type = 'grass' then 1 else 0 end) = 1                               as has_grass,
        max(case when c.surface_type = 'hard' then 1 else 0 end) = 1                                as has_hard,
        max(case when c.surface_type = 'turf' then 1 else 0 end) = 1                                as has_turf
    from {{ ref('dim_court') }} c
    join {{ ref('bridge_court_sport') }} b on b.court_id = c.court_id
    group by 1, 2
)

select
    v.venue_id,
    coalesce(v.venue_name, 'Unnamed courts')                  as venue_name,
    v.name_source,
    v.venue_source,
    s.sport_name,
    bvs.courts                                                as courts_for_sport,
    bvs.in_osm,
    bvs.in_places,
    bvs.in_manual,
    v.offerings,
    v.lat,
    v.lon,
    v.city,
    v.address_line,
    v.website,
    v.phone,
    v.opening_hours,
    v.google_place_id,
    -- court-level facts come from OSM; hand-curated venues carry their own surface and setting
    case when v.venue_source = 'manual' then v.has_indoor else coalesce(f.has_indoor, false) end     as has_indoor,
    case when v.venue_source = 'manual' then v.has_outdoor else coalesce(f.has_outdoor, false) end   as has_outdoor,
    case when v.venue_source = 'manual' then v.has_sand else coalesce(f.has_sand_beach, false) end   as has_sand_beach,
    coalesce(f.has_clay, false)                               as has_clay,
    coalesce(f.has_grass, false)                              as has_grass,
    coalesce(f.has_hard, false)                               as has_hard,
    coalesce(f.has_turf, false)                               as has_turf,
    v.has_lit_courts,
    v.is_confirmed_public,
    v.has_free_courts
from {{ ref('bridge_venue_sport') }} bvs
join {{ ref('dim_venue') }} v on v.venue_id = bvs.venue_id
join {{ ref('dim_sport') }} s on s.sport_id = bvs.sport_id
left join osm_facts f on f.venue_id = bvs.venue_id and f.sport_id = bvs.sport_id
