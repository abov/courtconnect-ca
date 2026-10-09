-- A place may be linked to a sport only once (the strongest evidence wins).
select place_id, sport_id, count(*) as n
from {{ ref('bridge_place_sport') }}
group by 1, 2
having count(*) > 1
