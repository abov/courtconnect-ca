-- "How complete is our data?" -- the honest-coverage dashboard.
select
    s.sport_name,
    s.popularity_class,
    count(distinct c.venue_id)                                          as venues_found,
    count(distinct b.court_id)                                          as courts_found,
    count(distinct case when c.access_type = 'public' then c.venue_id end) as public_venues,
    count(distinct case when c.access_type = 'public' then b.court_id end) as public_courts,
    count(distinct case when c.venue_unnamed then c.venue_id end)       as venues_missing_name,
    count(distinct case when c.is_free then b.court_id end)            as known_free_courts
from {{ ref('dim_sport') }} s
left join {{ ref('bridge_court_sport') }} b on b.sport_id = s.sport_id
left join (
    select ct.court_id, ct.venue_id, ct.access_type, ct.is_free, (v.name_source = 'unnamed') as venue_unnamed
    from {{ ref('dim_court') }} ct
    join {{ ref('dim_venue') }} v on v.venue_id = ct.venue_id
) c on c.court_id = b.court_id
where s.sport_family like 'Racket%'
group by 1, 2
order by courts_found desc
