-- Fails if any sport named on the sheet fails to reach dim_sport (e.g. lost in de-duplication or cleaning).
select s.sport
from {{ ref('all_racquet') }} s
left join {{ ref('dim_sport') }} d on d.sport_id = md5(lower(trim(s.sport)))
where trim(s.sport) <> '' and d.sport_id is null
