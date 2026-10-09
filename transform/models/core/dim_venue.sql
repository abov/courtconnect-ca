-- One row per facility: individual OSM courts rolled up by proximity (ADR 0003).
-- A venue inherits a name from any court or operator tag in its cluster.
with courts as (
    select * from {{ ref('dim_court') }}
),

sports as (
    select c.venue_id, count(distinct b.sport_id) as sport_count
    from courts c
    join {{ ref('bridge_court_sport') }} b on b.court_id = c.court_id
    group by 1
),

venues as (
    select
        venue_id,
        coalesce(min(court_name), min(operator_name))         as venue_name,
        case
            when min(court_name) is not null    then 'court_name'
            when min(operator_name) is not null then 'operator'
            else 'unnamed'
        end                                                   as name_source,
        count(*)                                              as court_records,
        avg(lat)                                              as lat,
        avg(lon)                                              as lon,
        max(case when is_lit then 1 else 0 end) = 1           as has_lit_courts,
        max(case when access_type = 'public' then 1 else 0 end) = 1 as is_confirmed_public,
        max(case when is_free then 1 else 0 end) = 1          as has_free_courts
    from courts
    group by venue_id
)

select
    v.*,
    coalesce(s.sport_count, 0)                                as sport_count
    {% if target.type == 'snowflake' %}
    , st_makepoint(v.lon, v.lat)                              as location  -- GEOGRAPHY, for ST_DWITHIN / ST_DISTANCE
    {% endif %}
from venues v
left join sports s on s.venue_id = v.venue_id
