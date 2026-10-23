-- Competition around each venue, per sport the venue is listed for: how many OTHER venues with the same sport sit within 5 and 15 miles
-- (straight-line). Known venues only, so it undercounts private clubs; INFERRED, not a market study. Null nearest_same_sport_mi = none within 15 miles.
with vs as (
    select
        venue_id,
        sport_name,
        any_value(venue_name)   as venue_name,
        any_value(city)         as city,
        any_value(region)       as region,
        max(courts_for_sport)   as courts_for_sport
    from {{ ref('mart_venue_finder') }}
    where lat is not null
      and sport_name not in (select trim(also_sport) from {{ ref('sport_also_played') }})
    group by 1, 2
)

select
    vs.venue_id,
    vs.venue_name,
    vs.city,
    vs.region,
    vs.sport_name,
    vs.courts_for_sport,
    count(distinct case when p.dist_mi <= 5 then p.other_venue_id end)    as same_sport_venues_5mi,
    count(distinct p.other_venue_id)                                      as same_sport_venues_15mi,
    round(min(p.dist_mi), 2)                                              as nearest_same_sport_mi,
    'inferred'                                                            as confirmation
from vs
left join {{ ref('int_venue_pairs_15mi') }} p
  on p.venue_id = vs.venue_id and p.sport_name = vs.sport_name
group by 1, 2, 3, 4, 5, 6
