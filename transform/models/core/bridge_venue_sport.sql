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
        coalesce(max(m.courts_count), 0)                      as courts,
        string_agg(distinct m.surface_type, ';')              as surfaces,
        string_agg(distinct m.access_type, ';')               as access_types
    from {{ ref('stg_manual_venues') }} m
    join {{ ref('int_manual_venue_match') }} mm on mm.venue_key = m.venue_key
    join {{ ref('dim_sport') }} s on s.sport_name = m.sport_name
    group by mm.effective_venue_id, s.sport_id
),

-- Sports a hand-curated venue lists also pass on their also-played sports (a pickleball seed row makes the venue a Skyball venue, like
-- an OSM pickleball court does). These rows are derived, so they carry no source flag; the finder mart drops the exclude_private_members
-- ones at members-only venues.
manual_also as (
    select m.venue_id, d.sport_id, m.courts
    from manual m
    join {{ ref('dim_sport') }} f on f.sport_id = m.sport_id
    join {{ ref('sport_also_played') }} a on trim(a.sport) = f.sport_name
    join {{ ref('dim_sport') }} d on d.sport_name = trim(a.also_sport)
    -- only_surfaces set (Soft Tennis: grass;turf): the hand-added venue must list one of those surfaces
    where (nullif(trim(a.only_surfaces), '') is null
           or list_has_any(string_split(m.surfaces, ';'), string_split(replace(a.only_surfaces, ' ', ''), ';')))
      -- only_access set (Micro Pickleball: public): the hand-added venue must be marked with one of those access values
      and (nullif(trim(a.only_access), '') is null
           or list_has_any(string_split(m.access_types, ';'), string_split(replace(a.only_access, ' ', ''), ';')))
),

unioned as (
    select venue_id, sport_id, courts, 1 as in_osm, 0 as in_places, 0 as in_manual from osm
    union all
    select venue_id, sport_id, 0, 0, 1, 0 from places
    union all
    select venue_id, sport_id, courts, 0, 0, 1 from manual
    union all
    select venue_id, sport_id, courts, 0, 0, 0 from manual_also
),

base as (
    select
        venue_id,
        sport_id,
        max(courts)                                           as courts,
        max(in_osm) = 1                                       as in_osm,
        max(in_places) = 1                                    as in_places,
        max(in_manual) = 1                                    as in_manual
    from unioned
    group by 1, 2
),

-- A person counted the courts of one sport at a venue and the OSM count is wrong (seeds/venue_court_counts.csv, e.g. 3 tennis-shaped pads
-- where imagery shows 2 tennis courts and the rest pickleball). Replaces the count only for a sport the venue already has, and only while
-- the pin is where it was checked (a row is ignored if no court of the venue lies within ~70 m of the checked position).
counted as (
    select o.venue_id, s.sport_id, cast(o.courts as integer) as courts
    from {{ ref('venue_court_counts') }} o
    join {{ ref('dim_sport') }} s on s.sport_name = trim(o.sport)
    where exists (
        select 1 from {{ ref('dim_court') }} c
        where c.venue_id = o.venue_id
          and abs(c.lat - cast(o.lat as double)) < 0.0007 and abs(c.lon - cast(o.lon as double)) < 0.0007)
),

-- Sports derived from the counted one (tennis courts also count for Frescotennis, Loboton, ...) follow it, but only where their count was just
-- the counted sport's own (a Skyball count raised by real pickleball courts is left alone).
cascaded as (
    select b.venue_id, b.sport_id, c.courts
    from counted c
    join {{ ref('dim_sport') }} f on f.sport_id = c.sport_id
    join {{ ref('sport_also_played') }} a on trim(a.sport) = f.sport_name
    join {{ ref('dim_sport') }} d on d.sport_name = trim(a.also_sport)
    join base src on src.venue_id = c.venue_id and src.sport_id = c.sport_id
    join base b on b.venue_id = c.venue_id and b.sport_id = d.sport_id and b.courts = src.courts
),

replacements as (
    select venue_id, sport_id, courts from counted
    union
    select venue_id, sport_id, courts from cascaded
)

select
    b.venue_id,
    b.sport_id,
    coalesce(r.courts, b.courts)                              as courts,
    b.in_osm,
    b.in_places,
    b.in_manual
from base b
left join replacements r on r.venue_id = b.venue_id and r.sport_id = b.sport_id
