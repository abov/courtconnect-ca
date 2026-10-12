-- A court can host several sports (e.g. a tennis court with pickleball lines).
-- Two seed files adjust what the OSM tags say:
--   sport_also_played.csv         : a court tagged sport A is also a court for sport B (racquetball courts host 4-wall paddle)
--   osm_court_sport_overrides.csv : a person found a tag wrong, so that court is not counted for that sport (verdict 'reject')
with tagged as (
    select distinct
        c.court_id,
        c.access_type,
        s.sport_name
    from {{ ref('stg_osm_courts') }} c
    join {{ ref('osm_sport_map') }} m
        on c.sport_tag_delimited like '%;' || m.osm_sport_key || ';%'
    join {{ ref('dim_sport') }} s
        on s.sport_name = m.sport
),

with_also as (
    select court_id, sport_name from tagged
    union
    select t.court_id, trim(a.also_sport)
    from tagged t
    join {{ ref('sport_also_played') }} a on trim(a.sport) = t.sport_name
    -- exclude_private_members = yes: private / members-only courts do not pass the sport on (Pitton on badminton courts)
    where not (lower(trim(coalesce(a.exclude_private_members, ''))) = 'yes' and t.access_type in ('private', 'members'))
)

select distinct
    w.court_id,
    s.sport_id
from with_also w
join {{ ref('dim_sport') }} s on s.sport_name = w.sport_name
left join {{ ref('osm_court_sport_overrides') }} o
    on trim(o.court_id) = w.court_id and trim(o.sport) = w.sport_name and lower(trim(o.verdict)) = 'reject'
where o.court_id is null
