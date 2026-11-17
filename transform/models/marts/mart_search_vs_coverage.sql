-- Where do people search for a sport but find few pins? One row per (metro, sport). Planning signal only: it is not shown in the app.
-- interest_index is Google Trends relative search interest (100 = the metro with the most searches for that sport in CA + NV, sampled; docs/search_interest_plan.md).
-- Venues are assigned to the NEAREST metro anchor within 120 miles (our own approximation, not the Nielsen/Google metro boundaries).
--   completeness_share : mean of the shares of those venues with a real name (court, operator, manual or places-directory name), an address and a usable website;
--                        the same three parts as the dashboard's completeness (ingestion/export_dashboard_data.py), leaving out likely private-residence pins
--                        (is_home_like, ADR 0016: they never get a street or a website). Null when no venues or only such pins.
--   Raw venue counts are not comparable across metros (a big metro, or one whose 120-mile catchment is wide, always has many). So both sides are put on
--   "100 = the average metro" scales and compared:
--   interest_vs_avg : 100 * interest_index / the sport's mean index over the metros with data. Trends already divides by each metro's total searches,
--                     so this is a share of local searches, not a head count.
--   usable_venues   : the sport's pins weighted by how findable they are (2026-11-17): each pin counts 0.5 for being a court plus 0.5 * the share of
--                     real name, address and usable website it has (0.5-1). Likely private-residence pins (is_home_like) count 0.5: by rule they never
--                     get a street or website, so they are not penalised as incomplete.
--   supply_index    : 100 * (usable_venues / the metro's pins) / (the same ratio over all the metros with data for that sport). The metro's pins
--                     (any sport, raw count) stand in for its size: no population seed, and the same catchment on both sides.
--                     usable_venues + 0.5 keeps a metro with no pins for the sport finite.
--   gap_score       : interest_vs_avg / supply_index. 1 = searched about as much as we list; 2 = twice as much searched as listed.
--   gap_candidate   : confidence 'ok', interest_vs_avg >= 100 (at least an average metro's searches), supply_index < 90 (clearly fewer pins than an
--                     average metro for its size; keeps a sport that already fills a metro, like Palm Springs tennis, out) and gap_score >= 1.5: a place to look for
--                     missing venues first, not proof of a gap. Thin sports are scored but never flagged (Trends samples them).
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

metro_pins as (
    select metro_code, count(distinct venue_id) as metro_pins
    from nearest
    group by 1
),

venues as (
    select metro_code, sport_name, count(distinct venue_id) as venues_found,
           sum(case when coalesce(is_home_like, false) then 0.5
                    else 0.5 + 0.5 * (coalesce(has_real_name, false)::int + coalesce(has_address, false)::int + coalesce(has_website, false)::int) / 3.0
               end)                                         as usable_venues,
           avg(has_real_name::int) filter (where not is_home_like) as real_name_share,
           avg(has_address::int) filter (where not is_home_like) as address_share,
           avg(has_website::int) filter (where not is_home_like) as website_share
    from nearest
    group by 1, 2
),

joined as (
    select
        i.*,
        coalesce(v.venues_found, 0)                                                  as venues_found,
        coalesce(v.usable_venues, 0)                                                 as usable_venues,
        mp.metro_pins,
        round((v.real_name_share + v.address_share + v.website_share) / 3, 4)        as completeness_share
    from {{ ref('int_search_interest') }} i
    left join venues v      on v.metro_code = i.metro_code and v.sport_name = i.sport
    left join metro_pins mp on mp.metro_code = i.metro_code
),

scored as (
    select
        *,
        100 * index_value / avg(index_value) over (partition by sport)                    as interest_vs_avg_raw,
        100 * ((usable_venues + 0.5) / nullif(metro_pins, 0))
            / nullif(sum(case when index_value is not null then usable_venues end) over (partition by sport)
                     / nullif(sum(case when index_value is not null then metro_pins end) over (partition by sport), 0), 0)
                                                                                           as supply_index_raw
    from joined
)

select
    metro_code,
    metro_name,
    sport                                                                         as sport_name,
    term                                                                          as search_term,
    index_value                                                                   as interest_index,
    index_source,
    confidence,
    venues_found,
    round(usable_venues, 1)                                                       as usable_venues,
    metro_pins,
    completeness_share,
    case when index_value is not null
         then rank() over (partition by sport order by index_value desc nulls last) end as interest_rank,
    round(interest_vs_avg_raw, 0)                                                 as interest_vs_avg,
    case when index_value is not null then round(supply_index_raw, 0) end          as supply_index,
    case when index_value is not null then round(interest_vs_avg_raw / supply_index_raw, 2) end as gap_score,
    coalesce(confidence = 'ok' and interest_vs_avg_raw >= 100 and supply_index_raw < 90 and interest_vs_avg_raw / supply_index_raw >= 1.5, false) as gap_candidate,
    exported_on
from scored
