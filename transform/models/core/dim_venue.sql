-- One row per facility: individual OSM courts rolled up by proximity (ADR 0003) and named (ADR 0004).
-- Name precedence: a name tagged on a court/facility > its operator > the smallest enclosing named
-- park / school / club (approximate, from bounding boxes) > unnamed.
with courts as (
    select * from {{ ref('dim_court') }}
),

sports as (
    select c.venue_id, count(distinct b.sport_id) as sport_count
    from courts c
    join {{ ref('bridge_court_sport') }} b on b.court_id = c.court_id
    group by 1
),

best_parent as (
    select venue_id, parent_name, parent_kind
    from (
        select
            venue_id, parent_name, parent_kind,
            row_number() over (partition by venue_id order by parent_area asc, parent_name) as rn
        from courts
        where parent_name is not null
    ) x
    where rn = 1
),

venues as (
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
)

select
    v.venue_id,
    coalesce(v.tagged_name, v.operator_name, p.parent_name)   as venue_name,
    case
        when v.tagged_name is not null   then 'court_name'
        when v.operator_name is not null then 'operator'
        when p.parent_name is not null   then 'enclosing_feature'
        else 'unnamed'
    end                                                       as name_source,
    case when v.tagged_name is null and v.operator_name is null then p.parent_kind end as name_feature_kind,
    v.court_records,
    v.facility_records,
    v.lat, v.lon,
    v.website, v.phone, v.opening_hours, v.address_line, v.city,
    v.has_lit_courts, v.is_confirmed_public, v.has_free_courts,
    v.has_indoor, v.has_outdoor,
    v.has_hard, v.has_clay, v.has_grass, v.has_turf, v.has_sand, v.has_indoor_floor,
    coalesce(s.sport_count, 0)                                as sport_count
    {% if target.type == 'snowflake' %}
    , st_makepoint(v.lon, v.lat)                              as location  -- GEOGRAPHY, for ST_DWITHIN / ST_DISTANCE
    {% endif %}
from venues v
left join sports s on s.venue_id = v.venue_id
left join best_parent p on p.venue_id = v.venue_id
