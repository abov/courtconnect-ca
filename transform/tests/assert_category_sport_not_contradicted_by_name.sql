-- An Overture tennis_court / tennis_stadium must not make a table tennis, padel or pickleball-only name a Tennis place
-- (bridge_place_sport drops a category sport when the name only names another distinctive sport). Add a place_sport_overrides
-- confirm instead if one of these really does have tennis courts.
select p.place_name
from {{ ref('dim_place') }} p
join {{ ref('bridge_place_sport') }} bp on bp.place_id = p.place_id and bp.match_type = 'category'
join {{ ref('dim_sport') }} s on s.sport_id = bp.sport_id and s.sport_name = 'Tennis'
where p.place_name like '%Table Tennis%'
   or p.place_name like '%Padel%'
   or (p.place_name like '%Pickleball%' and p.place_name not like '%Tennis%')
