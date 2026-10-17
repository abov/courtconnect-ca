-- A court can host several sports (e.g. a tennis court with pickleball lines).
-- Two seed files adjust what the OSM tags say:
--   sport_also_played.csv         : a court tagged sport A is also a court for sport B (racquetball courts host 4-wall paddle)
--   osm_court_sport_overrides.csv : a person found a tag wrong, so that court is not counted for that sport (verdict 'reject');
--                                   optional correct_sport = the sport it really is (e.g. aerial 'padel' tag on pickleball courts)
with tagged as (
    select
        c.court_id,
        c.access_type,
        s.sport_name
    from {{ ref('stg_osm_courts') }} c
    join {{ ref('osm_sport_map') }} m
        on c.sport_tag_delimited like '%;' || m.osm_sport_key || ';%'
    join {{ ref('dim_sport') }} s
        on s.sport_name = m.sport

    union

    -- a rejected tag that a person re-identified (correct_sport): the court counts for the real sport instead
    select
        c.court_id,
        c.access_type,
        trim(o.correct_sport) as sport_name
    from {{ ref('osm_court_sport_overrides') }} o
    join {{ ref('stg_osm_courts') }} c on c.court_id = trim(o.court_id)
    where lower(trim(o.verdict)) = 'reject'
      and nullif(trim(o.correct_sport), '') is not null
),

with_also as (
    select court_id, sport_name from tagged
    union
    select t.court_id, trim(a.also_sport)
    from tagged t
    join {{ ref('sport_also_played') }} a on trim(a.sport) = t.sport_name
    -- a rejected tag passes nothing on either (Venice Beach: Tennis rejected, so no Frescotennis / Loboton / Tennis Triples)
    left join {{ ref('osm_court_sport_overrides') }} r
        on trim(r.court_id) = t.court_id and trim(r.sport) = t.sport_name and lower(trim(r.verdict)) = 'reject'
    -- exclude_private_members = yes: private / members-only courts do not pass the sport on (Pitton on badminton courts)
    where r.court_id is null
      and not (lower(trim(coalesce(a.exclude_private_members, ''))) = 'yes' and t.access_type in ('private', 'members'))
)

select distinct
    w.court_id,
    s.sport_id
from with_also w
join {{ ref('dim_sport') }} s on s.sport_name = w.sport_name
left join {{ ref('osm_court_sport_overrides') }} o
    on trim(o.court_id) = w.court_id and trim(o.sport) = w.sport_name and lower(trim(o.verdict)) = 'reject'
where o.court_id is null
