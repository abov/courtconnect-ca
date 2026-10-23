-- Internal consistency of the market marts: (venue, sport) is unique in mart_venue_neighbors, a sport "to try nearby" is never one the venue
-- already lists, and a city marked 'served' has at least one venue.
select 'duplicate_neighbor_row' as problem, venue_id || '|' || sport_name as detail
from {{ ref('mart_venue_neighbors') }}
group by venue_id, sport_name
having count(*) > 1

union all

select 'nearby_sport_also_listed_at_venue', n.venue_id || '|' || n.sport_name
from {{ ref('mart_venue_nearby_sports') }} n
join {{ ref('mart_venue_neighbors') }} v on v.venue_id = n.venue_id and v.sport_name = n.sport_name

union all

select 'served_without_venue', city || '|' || sport_name
from {{ ref('mart_market_gaps') }}
where gap_status = 'served' and venues_in_city = 0
