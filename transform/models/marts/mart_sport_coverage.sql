-- "How complete is our data?" -- the honest-coverage dashboard.
select
    s.sport_name,
    s.popularity_class,
    count(distinct b.court_id)                                          as courts_found,
    count(distinct case when c.access_type = 'public' then b.court_id end) as public_courts,
    count(distinct case when c.name_missing then b.court_id end)        as courts_missing_name,
    count(distinct case when c.is_free then b.court_id end)            as known_free_courts
from {{ ref('dim_sport') }} s
left join {{ ref('bridge_court_sport') }} b on b.sport_id = s.sport_id
left join (
    select court_id, access_type, is_free, (court_name is null) as name_missing
    from {{ ref('dim_court') }}
) c on c.court_id = b.court_id
where s.sport_family = 'Racket'
group by 1, 2
order by courts_found desc
