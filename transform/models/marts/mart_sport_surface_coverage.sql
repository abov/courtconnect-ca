-- Courts and venues per sport, split by playing surface and indoor/outdoor setting.
-- Answers "where can I play padel on sand?", "any indoor clay in California?", "grass courts?".
select
    s.sport_name,
    c.surface_type,
    c.setting,
    count(distinct c.court_id)                                as courts,
    count(distinct c.venue_id)                                as venues,
    count(distinct case when c.access_type = 'public' then c.venue_id end) as public_venues
from {{ ref('bridge_court_sport') }} b
join {{ ref('dim_court') }} c on c.court_id = b.court_id
join {{ ref('dim_sport') }} s on s.sport_id = b.sport_id
where c.record_kind = 'court'
group by 1, 2, 3
