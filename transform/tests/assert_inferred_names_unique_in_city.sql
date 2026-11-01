-- Venues whose name is only inferred (name_source 'enclosing_feature') must not share a displayed name inside a city: where the raw name is
-- shared, int_venue_display_name adds a "(direction courts, N courts[, #k])" suffix. A row here is two such pins that still look identical.
select lower(venue_name) as venue_name, lower(city) as city, count(distinct venue_id) as venues
from {{ ref('mart_venue_finder') }}
where name_source = 'enclosing_feature' and city is not null
group by 1, 2
having count(distinct venue_id) > 1
