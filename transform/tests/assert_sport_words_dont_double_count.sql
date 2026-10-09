-- A "Table Tennis Association" must count as Table Tennis, not also as plain Tennis (the longest matching phrase wins).
select p.place_name
from {{ ref('dim_place') }} p
join {{ ref('bridge_place_sport') }} bp on bp.place_id = p.place_id and bp.match_type = 'name_keyword'
join {{ ref('dim_sport') }} s on s.sport_id = bp.sport_id and s.sport_name = 'Tennis'
where p.category not in ('tennis_court', 'tennis_stadium')
  and (p.place_name like '%Table Tennis%' or p.place_name like '%Platform Tennis%' or p.place_name like '%Beach Tennis%')
