-- A court can host several sports (e.g. a tennis court with pickleball lines).
select distinct
    c.court_id,
    s.sport_id
from {{ ref('stg_osm_courts') }} c
join {{ ref('osm_sport_map') }} m
    on c.sport_tag_delimited like '%;' || m.osm_sport_key || ';%'
join {{ ref('dim_sport') }} s
    on s.sport_name = m.sport
