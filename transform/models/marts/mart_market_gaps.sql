-- Where is a racket sport missing? One row per (city, sport) for every city with a mapped racket venue and every sport we list directly.
-- The city point is the average of its venues' coordinates (INFERRED, not the true center); distances are straight-line miles.
--   venues_in_city        : venues for the sport in the city
--   venues_within_15mi    : venues for the sport within 15 miles of that point
--   gap_status            : 'served' | 'nearby' (none in the city, one within 15 miles) | 'no_venue_within_15mi'
--   racket_venues_in_city : all directly listed racket venues in the city, a rough activity proxy (no population yet)
--   sport_coverage_status : from mart_sport_gaps; when the sport is sparse or unmapped, a gap may be missing data, not a real gap
with vs as (
    select
        venue_id,
        sport_name,
        upper(trim(any_value(city)))     as city_key,   -- Overture cities arrive in capitals ('IRVINE'), OSM in mixed case: match on the capitals
        any_value(city)                  as city_raw,
        any_value(region)                as region,
        any_value(lat)                   as lat,
        any_value(lon)                   as lon,
        max(courts_for_sport)            as courts,
        bool_or(is_confirmed_public)     as is_confirmed_public,
        bool_or(is_members_only)         as is_members_only
    from {{ ref('mart_venue_finder') }}
    where lat is not null
      and sport_name not in (select trim(also_sport) from {{ ref('sport_also_played') }})
    group by 1, 2
),

cities as (
    select
        region,
        city_key,
        coalesce(min(case when city_raw <> upper(city_raw) then city_raw end), min(city_raw))   as city,   -- prefer the mixed-case spelling for display
        avg(lat)                         as lat,
        avg(lon)                         as lon,
        count(distinct venue_id)         as racket_venues_in_city
    from vs
    where city_raw is not null
    group by 1, 2
),

sports as (
    select distinct sport_name from vs
),

in_city as (
    select
        region, city_key, sport_name,
        count(distinct venue_id)                                                  as venues_in_city,
        coalesce(sum(courts), 0)                                                  as courts_in_city,
        count(distinct case when is_confirmed_public then venue_id end)           as public_venues_in_city,
        count(distinct case when is_members_only then venue_id end)               as members_only_venues_in_city
    from vs
    where city_raw is not null
    group by 1, 2, 3
),

near as (
    select
        c.region, c.city_key, v.sport_name,
        count(distinct case when {{ distance_mi('c.lat', 'c.lon', 'v.lat', 'v.lon') }} <= 15 then v.venue_id end) as venues_within_15mi,
        min({{ distance_mi('c.lat', 'c.lon', 'v.lat', 'v.lon') }})                                              as nearest_mi
    from cities c
    join vs v on abs(v.lat - c.lat) < 1.5 and abs(v.lon - c.lon) < 2.0   -- ~100 miles: wide prefilter so far-off nearest venues are still found
    group by 1, 2, 3
)

select
    c.region,
    c.city,
    s.sport_name,
    c.racket_venues_in_city,
    coalesce(i.venues_in_city, 0)                                             as venues_in_city,
    coalesce(i.courts_in_city, 0)                                             as courts_in_city,
    coalesce(i.public_venues_in_city, 0)                                      as public_venues_in_city,
    coalesce(i.members_only_venues_in_city, 0)                                as members_only_venues_in_city,
    coalesce(n.venues_within_15mi, 0)                                         as venues_within_15mi,
    round(n.nearest_mi, 1)                                                    as nearest_mi,   -- null = none within ~100 miles
    case
        when coalesce(i.venues_in_city, 0) > 0         then 'served'
        when coalesce(n.venues_within_15mi, 0) > 0     then 'nearby'
        else 'no_venue_within_15mi'
    end                                                                       as gap_status,
    g.coverage_status                                                         as sport_coverage_status,
    'inferred'                                                                as confirmation
from cities c
cross join sports s
left join in_city i on i.region = c.region and i.city_key = c.city_key and i.sport_name = s.sport_name
left join near n    on n.region = c.region and n.city_key = c.city_key and n.sport_name = s.sport_name
left join {{ ref('mart_sport_gaps') }} g on g.sport_name = s.sport_name
