-- "How complete is our data?" One row per racket sport, including sports with zero venues found.
-- venues_found counts only evidence we trust: OSM courts, and places with a racket category or a distinctive sport word.
with weak as (
    select sport_id, count(distinct place_id) as weak_places
    from {{ ref('bridge_place_sport') }}
    where evidence = 'weak'
    group by 1
)

select
    s.sport_name,
    s.popularity_class,
    count(distinct bvs.venue_id)                                                       as venues_found,
    count(distinct case when bvs.in_osm then bvs.venue_id end)                         as osm_venues,
    count(distinct case when bvs.in_places then bvs.venue_id end)                      as places_venues,
    count(distinct case when bvs.in_osm and bvs.in_places then bvs.venue_id end)       as venues_in_both,
    coalesce(sum(bvs.courts), 0)                                                       as courts_found,
    count(distinct case when v.is_confirmed_public then bvs.venue_id end)              as public_venues,
    count(distinct case when v.name_source = 'unnamed' then bvs.venue_id end)          as venues_missing_name,
    count(distinct case when v.name_source <> 'unnamed' then bvs.venue_id end)         as venues_named,
    coalesce(max(w.weak_places), 0)                                                    as weak_name_matches
from {{ ref('dim_sport') }} s
left join {{ ref('bridge_venue_sport') }} bvs on bvs.sport_id = s.sport_id
left join {{ ref('dim_venue') }} v on v.venue_id = bvs.venue_id
left join weak w on w.sport_id = s.sport_id
where s.sport_family like 'Racket%'
group by 1, 2
