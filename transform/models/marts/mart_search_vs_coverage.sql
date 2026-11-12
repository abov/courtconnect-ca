-- Where do people search for a sport but find few pins? One row per (metro, sport). Planning signal only: it is not shown in the app.
-- interest_index is Google Trends relative search interest (100 = the metro with the most searches for that sport in CA + NV, sampled; docs/search_interest_plan.md).
-- Venues are assigned to the NEAREST metro anchor within 120 miles (our own approximation, not the Nielsen/Google metro boundaries).
--   completeness_share : mean of the shares of those venues with a real name (court, operator, manual or places-directory name), an address and a usable website;
--                        the same three parts as the dashboard's completeness (ingestion/export_dashboard_data.py), leaving out likely private-residence pins
--                        (is_home_like, ADR 0016: they never get a street or a website). Null when no venues or only such pins.
--   gap_candidate : confidence 'ok', index >= 50 and 3 or fewer venues for the sport: a place to look for missing venues first, not proof of a gap
with metro as (
    select metro_code, metro_name, anchor_lat, anchor_lon from {{ ref('search_metros') }}
),

vs as (
    select venue_id, sport_name, any_value(lat) as lat, any_value(lon) as lon,
           any_value(name_source in ('court_name', 'operator', 'manual', 'places_directory')) as has_real_name,
           any_value(address_line is not null)                                                as has_address,
           any_value(website_usable is not null)                                              as has_website,
           any_value(is_home_like)                                                            as is_home_like
    from {{ ref('mart_venue_finder') }}
    where lat is not null
      and sport_name not in (select trim(also_sport) from {{ ref('sport_also_played') }})
    group by 1, 2
),

nearest as (
    select venue_id, sport_name, metro_code, has_real_name, has_address, has_website, is_home_like
    from (
        select
            v.venue_id, v.sport_name, m.metro_code, v.has_real_name, v.has_address, v.has_website, v.is_home_like,
            row_number() over (partition by v.venue_id, v.sport_name
                               order by {{ distance_mi('m.anchor_lat', 'm.anchor_lon', 'v.lat', 'v.lon') }}) as rn,
            {{ distance_mi('m.anchor_lat', 'm.anchor_lon', 'v.lat', 'v.lon') }}                               as dist_mi
        from vs v
        cross join metro m
    )
    where rn = 1 and dist_mi <= 120
),

venues as (
    select metro_code, sport_name, count(distinct venue_id) as venues_found,
           avg(has_real_name::int) filter (where not is_home_like) as real_name_share,
           avg(has_address::int) filter (where not is_home_like) as address_share,
           avg(has_website::int) filter (where not is_home_like) as website_share
    from nearest
    group by 1, 2
)

select
    i.metro_code,
    i.metro_name,
    i.sport                                                                       as sport_name,
    i.term                                                                        as search_term,
    i.index_value                                                                 as interest_index,
    i.index_source,
    i.confidence,
    coalesce(v.venues_found, 0)                                                   as venues_found,
    round((v.real_name_share + v.address_share + v.website_share) / 3, 4)         as completeness_share,
    case when i.index_value is not null
         then rank() over (partition by i.sport order by i.index_value desc nulls last) end as interest_rank,
    coalesce(i.confidence = 'ok' and i.index_value >= 50 and coalesce(v.venues_found, 0) <= 3, false) as gap_candidate,
    i.exported_on
from {{ ref('int_search_interest') }} i
left join venues v on v.metro_code = i.metro_code and v.sport_name = i.sport
