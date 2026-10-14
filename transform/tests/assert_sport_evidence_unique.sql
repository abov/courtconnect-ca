-- One ladder row per (venue, sport), and every venue-sport the finder lists has one.
select venue_id, sport_id, count(*) as n
from {{ ref('mart_sport_evidence') }}
group by 1, 2
having count(*) > 1
union all
select b.venue_id, b.sport_id, 0
from {{ ref('bridge_venue_sport') }} b
left join {{ ref('mart_sport_evidence') }} e on e.venue_id = b.venue_id and e.sport_id = b.sport_id
where e.venue_id is null
