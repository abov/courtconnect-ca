-- Which sports are played at which venue, and which source says so.
-- OpenStreetMap contributes court counts; places contribute only STRONG evidence (a racket category or a distinctive sport word).
-- Weak name matches stay in bridge_place_sport and mart_places_to_review.
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
    select p.venue_id, bp.sport_id, count(distinct p.place_id) as places
    from {{ ref('dim_place') }} p
    join {{ ref('bridge_place_sport') }} bp on bp.place_id = p.place_id and bp.evidence = 'strong'
    group by 1, 2
)

select
    coalesce(o.venue_id, p.venue_id)                          as venue_id,
    coalesce(o.sport_id, p.sport_id)                          as sport_id,
    coalesce(o.courts, 0)                                     as courts,
    o.venue_id is not null                                    as in_osm,
    p.venue_id is not null                                    as in_places
from osm o
full outer join places p on p.venue_id = o.venue_id and p.sport_id = o.sport_id
