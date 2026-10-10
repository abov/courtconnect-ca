-- Which sports are played at which venue, and which source says so.
-- OSM contributes court counts; places contribute only STRONG evidence (a racket category or a distinctive sport word);
-- manual venues are hand-curated entries. Weak name matches stay in bridge_place_sport and mart_places_to_review.
with osm as (
    select
        c.venue_id,
        b.sport_id,
        count(distinct case when c.record_kind = 'court' then c.court_id end) as courts
    from {{ ref('dim_court') }} c
    join {{ ref('bridge_court_sport') }} b on b.court_id = c.court_id
    group by 1, 2
),

places as (
    select distinct p.venue_id, bp.sport_id
    from {{ ref('dim_place') }} p
    join {{ ref('bridge_place_sport') }} bp on bp.place_id = p.place_id and bp.evidence = 'strong'
),

-- A manual venue attaches to the venue it matched (see int_manual_venue_match). Its court count is per sport (a park's OSM
-- courts may be tennis while the hand-added ones are paddle tennis), and where both sources count the same sport we take the
-- larger number instead of adding them.
manual as (
    select
        mm.effective_venue_id                                 as venue_id,
        s.sport_id,
        coalesce(max(m.courts_count), 0)                      as courts
    from {{ ref('stg_manual_venues') }} m
    join {{ ref('int_manual_venue_match') }} mm on mm.venue_key = m.venue_key
    join {{ ref('dim_sport') }} s on s.sport_name = m.sport_name
    group by mm.effective_venue_id, s.sport_id
),

unioned as (
    select venue_id, sport_id, courts, 1 as in_osm, 0 as in_places, 0 as in_manual from osm
    union all
    select venue_id, sport_id, 0, 0, 1, 0 from places
    union all
    select venue_id, sport_id, courts, 0, 0, 1 from manual
)

select
    venue_id,
    sport_id,
    max(courts)                                               as courts,
    max(in_osm) = 1                                           as in_osm,
    max(in_places) = 1                                        as in_places,
    max(in_manual) = 1                                        as in_manual
from unioned
group by 1, 2
