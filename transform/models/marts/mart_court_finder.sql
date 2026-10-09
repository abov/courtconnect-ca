-- What the app queries: one row per (court, sport) with everything a player needs.
select
    c.court_id,
    c.court_name,
    s.sport_name,
    c.lat,
    c.lon,
    c.surface_type,
    c.is_lit,
    c.access_type,
    c.is_free,
    c.courts_count
from {{ ref('dim_court') }} c
join {{ ref('bridge_court_sport') }} b on b.court_id = c.court_id
join {{ ref('dim_sport') }} s on s.sport_id = b.sport_id
