-- "How complete is our data?" One row per racket sport, including sports with zero courts found.
select
    s.sport_name,
    s.popularity_class,
    count(distinct c.venue_id)                                                         as venues_found,
    count(distinct case when c.record_kind = 'court' then c.court_id end)              as courts_found,
    count(distinct case when c.access_type = 'public' then c.venue_id end)             as public_venues,
    count(distinct case when v.name_source = 'unnamed' then c.venue_id end)            as venues_missing_name,
    count(distinct case when v.name_source <> 'unnamed' then c.venue_id end)           as venues_named
from {{ ref('dim_sport') }} s
left join {{ ref('bridge_court_sport') }} b on b.sport_id = s.sport_id
left join {{ ref('dim_court') }} c on c.court_id = b.court_id
left join {{ ref('dim_venue') }} v on v.venue_id = c.venue_id
where s.sport_family like 'Racket%'
group by 1, 2
