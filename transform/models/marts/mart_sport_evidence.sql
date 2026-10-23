-- Sport-evidence ladder: for each (venue, sport), the STRONGEST reason we think the sport is played there, and how many rungs agree.
-- Why: a sport label can be wrong while the venue is right (2026-10-13: OSM `pelota` was read as Peruvian Paleta frontón at Basque clubs).
-- A label resting on the lowest rungs is a candidate for review, and the confidence score can use the rung instead of treating all labels alike.
--   rung 1  confirmed   : hand-added venue with confirmation visited / official, or a human 'confirm' in place_sport_overrides
--   rung 2  reported    : hand-added venue, confirmation reported (owner / community report)
--   rung 3  osm_tag     : OpenStreetMap `sport=` tag we map with HIGH confidence (osm_sport_map)
--   rung 4  osm_tag_loose : OSM tag mapped with MEDIUM confidence (tag is a family name, e.g. pelota, paddle_tennis)
--   rung 5  overture_category : Overture classifies the place as a racket venue for that sport
--   rung 6  name_keyword : a distinctive sport word in the business name (inferred from the name only)
--   rung 7  derived     : only reachable through sport_also_played (a pickleball court is also a Skyball court); an inference, not a sighting
-- Weak (ambiguous) name matches are not venues and never appear here. Rungs 1-2 come from people, 3-6 from datasets, 7 from rules.
with osm as (
    select distinct
        c.venue_id,
        s.sport_id,
        case when m.confidence = 'high' then 3 else 4 end as rung
    from {{ ref('dim_court') }} c
    join {{ ref('stg_osm_courts') }} t on t.court_id = c.court_id
    join {{ ref('osm_sport_map') }} m on t.sport_tag_delimited like '%;' || m.osm_sport_key || ';%'
    join {{ ref('dim_sport') }} s on s.sport_name = m.sport
    left join {{ ref('osm_court_sport_overrides') }} o
        on trim(o.court_id) = c.court_id and trim(o.sport) = s.sport_name and lower(trim(o.verdict)) = 'reject'
    where o.court_id is null

    union

    -- a human re-identified a wrong OSM tag (correct_sport), from imagery or a page: counts as a loose label, so it stays in the review queue
    select distinct c.venue_id, s.sport_id, 4 as rung
    from {{ ref('osm_court_sport_overrides') }} o
    join {{ ref('dim_court') }} c on c.court_id = trim(o.court_id)
    join {{ ref('dim_sport') }} s on s.sport_name = trim(o.correct_sport)
    where lower(trim(o.verdict)) = 'reject'
      and nullif(trim(o.correct_sport), '') is not null
),

places as (
    select distinct
        p.venue_id,
        bp.sport_id,
        case
            when bp.match_type = 'manual' then 1
            when bp.match_type = 'category' then 5
            when bp.match_type = 'name_keyword' then 6
        end as rung
    from {{ ref('dim_place') }} p
    join {{ ref('bridge_place_sport') }} bp on bp.place_id = p.place_id and bp.evidence = 'strong'
    where bp.match_type in ('manual', 'category', 'name_keyword')
),

manual as (
    select
        mm.effective_venue_id as venue_id,
        s.sport_id,
        min(case when m.confirmation_level in ('visited', 'official') then 1 else 2 end) as rung
    from {{ ref('stg_manual_venues') }} m
    join {{ ref('int_manual_venue_match') }} mm on mm.venue_key = m.venue_key
    join {{ ref('dim_sport') }} s on s.sport_name = m.sport_name
    group by 1, 2
),

direct as (
    select * from osm
    union all select * from places
    union all select * from manual
),

per_pair as (
    select venue_id, sport_id, min(rung) as best_rung, count(distinct rung) as rungs_agreeing
    from direct
    group by 1, 2
),

-- every (venue, sport) the finder knows; pairs with no direct rung are derived (rung 7)
all_pairs as (
    select b.venue_id, b.sport_id, coalesce(p.best_rung, 7) as best_rung, coalesce(p.rungs_agreeing, 0) as rungs_agreeing
    from {{ ref('bridge_venue_sport') }} b
    left join per_pair p on p.venue_id = b.venue_id and p.sport_id = b.sport_id
)

select
    a.venue_id,
    a.sport_id,
    s.sport_name,
    a.best_rung,
    case a.best_rung
        when 1 then 'confirmed' when 2 then 'reported' when 3 then 'osm_tag' when 4 then 'osm_tag_loose'
        when 5 then 'overture_category' when 6 then 'name_keyword' else 'derived'
    end                                               as best_rung_label,
    a.rungs_agreeing,
    -- needs_review: the label rests only on a loose OSM tag or a business-name word, so a wrong label is plausible.
    -- Derived rows (rung 7) are rule outputs documented in sport_also_played.csv, so they are not queued here.
    a.best_rung in (4, 6)                              as needs_review,
    'inferred'                                         as confirmation_note   -- ladder position is our judgement, not a venue's own statement
from all_pairs a
join {{ ref('dim_sport') }} s on s.sport_id = a.sport_id
