-- One row per facility.
--   venue_source 'osm'         : courts grouped by proximity (ADR 0003), no matching place
--   venue_source 'osm+places'  : the same, plus an Overture place within `place_match_radius_m` that adds a name, website, phone, address
--   venue_source 'places_only' : a racket-sport place Overture knows about that OpenStreetMap has no court for (indoor clubs, gyms...)
-- Name precedence: tagged on the court > operator > Overture place name (confidence >= 0.5) > enclosing park/school/club
-- (approximate, ADR 0004) > unnamed.
with courts as (
    select * from {{ ref('dim_court') }}
),

sports as (
    select venue_id, count(distinct sport_id) as sport_count
    from {{ ref('bridge_venue_sport') }}
    group by 1
),

best_parent as (
    select venue_id, parent_name, parent_kind
    from (
        select venue_id, parent_name, parent_kind,
               row_number() over (partition by venue_id order by parent_area asc, parent_name) as rn
        from courts
        where parent_name is not null
    ) x
    where rn = 1
),

best_place as (
    select matched_venue_id as venue_id, place_name, website, phone, address_line, city, confidence
    from (
        select *, row_number() over (partition by matched_venue_id order by confidence desc, place_id) as rn
        from {{ ref('dim_place') }}
        where matched_venue_id is not null and has_strong_sport
    ) x
    where rn = 1
),

osm_venues as (
    select
        venue_id,
        min(court_name)                                       as tagged_name,
        min(operator_name)                                    as operator_name,
        sum(case when record_kind = 'court' then 1 else 0 end)    as court_records,
        sum(case when record_kind = 'facility' then 1 else 0 end) as facility_records,
        avg(lat)                                              as lat,
        avg(lon)                                              as lon,
        min(website)                                          as website,
        min(phone)                                            as phone,
        min(opening_hours)                                    as opening_hours,
        min(address_line)                                     as address_line,
        min(city)                                             as city,
        max(case when is_lit then 1 else 0 end) = 1                   as has_lit_courts,
        max(case when access_type = 'public' then 1 else 0 end) = 1   as is_confirmed_public,
        max(case when is_free then 1 else 0 end) = 1                  as has_free_courts,
        max(case when setting = 'indoor' then 1 else 0 end) = 1       as has_indoor,
        max(case when setting in ('outdoor', 'likely_outdoor', 'covered') then 1 else 0 end) = 1 as has_outdoor,
        max(case when surface_type = 'hard' then 1 else 0 end) = 1    as has_hard,
        max(case when surface_type = 'clay' then 1 else 0 end) = 1    as has_clay,
        max(case when surface_type = 'grass' then 1 else 0 end) = 1   as has_grass,
        max(case when surface_type = 'turf' then 1 else 0 end) = 1    as has_turf,
        max(case when surface_type = 'sand' then 1 else 0 end) = 1    as has_sand,
        max(case when surface_type in ('carpet', 'wood') then 1 else 0 end) = 1 as has_indoor_floor
    from courts
    group by venue_id
),

osm_final as (
    select
        v.venue_id,
        coalesce(v.tagged_name, v.operator_name,
                 case when pl.confidence >= 0.5 then pl.place_name end, pp.parent_name)   as venue_name,
        case
            when v.tagged_name is not null                      then 'court_name'
            when v.operator_name is not null                    then 'operator'
            when pl.confidence >= 0.5                           then 'places_directory'
            when pp.parent_name is not null                     then 'enclosing_feature'
            else 'unnamed'
        end                                                   as name_source,
        case when v.tagged_name is null and v.operator_name is null
                  and coalesce(pl.confidence, 0) < 0.5 then pp.parent_kind end            as name_feature_kind,
        case when pl.venue_id is not null then 'osm+places' else 'osm' end                as venue_source,
        v.court_records,
        v.facility_records,
        v.lat, v.lon,
        coalesce(v.website, pl.website)                       as website,
        coalesce(v.phone, pl.phone)                           as phone,
        v.opening_hours,
        coalesce(v.address_line, pl.address_line)             as address_line,
        coalesce(v.city, pl.city)                             as city,
        cast(null as varchar)                                 as offerings,
        v.has_lit_courts, v.is_confirmed_public, v.has_free_courts,
        v.has_indoor, v.has_outdoor,
        v.has_hard, v.has_clay, v.has_grass, v.has_turf, v.has_sand, v.has_indoor_floor
    from osm_venues v
    left join best_parent pp on pp.venue_id = v.venue_id
    left join best_place pl on pl.venue_id = v.venue_id
),

places_only as (
    select
        p.venue_id,
        p.place_name                                          as venue_name,
        'places_directory'                                    as name_source,
        cast(null as varchar)                                 as name_feature_kind,
        'places_only'                                         as venue_source,
        0                                                     as court_records,
        1                                                     as facility_records,
        p.lat, p.lon,
        p.website, p.phone,
        cast(null as varchar)                                 as opening_hours,
        p.address_line, p.city,
        cast(null as varchar)                                 as offerings,
        false as has_lit_courts, false as is_confirmed_public, false as has_free_courts,
        false as has_indoor, false as has_outdoor,
        false as has_hard, false as has_clay, false as has_grass, false as has_turf, false as has_sand, false as has_indoor_floor
    from {{ ref('dim_place') }} p
    where p.matched_venue_id is null and p.has_strong_sport
),

-- Hand-curated venues (seeds/manual_venues.csv): one row per venue, with what it offers.
manual_final as (
    select
        venue_id,
        min(venue_name)                                       as venue_name,
        'manual'                                              as name_source,
        cast(null as varchar)                                 as name_feature_kind,
        'manual'                                              as venue_source,
        0                                                     as court_records,
        1                                                     as facility_records,
        min(lat)                                              as lat,
        min(lon)                                              as lon,
        min(website)                                          as website,
        cast(null as varchar)                                 as phone,
        cast(null as varchar)                                 as opening_hours,
        cast(null as varchar)                                 as address_line,
        min(city)                                             as city,
        min(offerings)                                        as offerings,
        false as has_lit_courts, false as is_confirmed_public, false as has_free_courts,
        max(case when setting = 'indoor' then 1 else 0 end) = 1                               as has_indoor,
        max(case when setting in ('outdoor', 'likely_outdoor', 'covered') then 1 else 0 end) = 1 as has_outdoor,
        max(case when surface_type = 'hard' then 1 else 0 end) = 1    as has_hard,
        max(case when surface_type = 'clay' then 1 else 0 end) = 1    as has_clay,
        max(case when surface_type = 'grass' then 1 else 0 end) = 1   as has_grass,
        max(case when surface_type = 'turf' then 1 else 0 end) = 1    as has_turf,
        max(case when surface_type = 'sand' then 1 else 0 end) = 1    as has_sand,
        false as has_indoor_floor
    from {{ ref('stg_manual_venues') }}
    group by venue_id
),

unioned as (
    select * from osm_final
    union all
    select * from places_only
    union all
    select * from manual_final
)

select
    u.*,
    {{ website_status('u.website', 'wc.status') }}            as website_status,   -- ok | dead | unknown | unchecked; null = no website
    g.google_place_id,                                         -- ID only; the app fetches details live (ADR 0005)
    coalesce(s.sport_count, 0)                                as sport_count
    {% if target.type == 'snowflake' %}
    , st_makepoint(u.lon, u.lat)                              as location  -- GEOGRAPHY, for ST_DWITHIN / ST_DISTANCE
    {% endif %}
from unioned u
left join sports s on s.venue_id = u.venue_id
left join {{ ref('stg_google_place_ids') }} g on g.venue_id = u.venue_id
left join {{ ref('stg_website_checks') }} wc on wc.domain = {{ website_domain('u.website') }}
