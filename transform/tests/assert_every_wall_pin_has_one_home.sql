-- ADR 0032: every hitting-wall pin is either a feature of one court venue (int_wall_venue_link) or a venue of its own, never both, never neither.
select 'wall_pin_count_mismatch'
where (select count(*) from {{ ref('mart_wall_pins') }})
   <> (select count(*) from {{ ref('int_wall_venue_link') }}) + (select count(*) from {{ ref('int_wall_venue') }})
union all
select w.wall_key
from {{ ref('mart_wall_pins') }} w
join {{ ref('int_wall_venue_link') }} l on l.wall_key = w.wall_key
join {{ ref('int_wall_venue') }} v on v.venue_id = md5('wall:' || w.wall_key)
