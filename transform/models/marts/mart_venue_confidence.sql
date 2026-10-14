-- Rule-based confidence score per venue (0-100): how well backed up is the fact that this venue exists with these sports.
-- It is a transparent, INFERRED heuristic ("rules_v1"), not a probability: every point comes from a column you can read here.
--   sources   0-30  one source 10, two 20, three 30 (OpenStreetMap, Overture places, hand-added)
--   evidence  0-25  best hand-added confirmation: visited 25, official 20, reported 8
--   named     0-10  a real name (hand-added, Overture, court name or operator), not a guessed or empty one
--   contact   0-20  usable website 8, phone 4, opening hours 4, address 4
--   fresh     0-15  newest dated check (hand-added confirmation or link-out verification): <=35 days 15, <=90 days 8
-- Bands: high >= 60, medium 30-59, low < 30.
with src as (
    select
        venue_id,
        max(case when in_osm then 1 else 0 end)    as has_osm,
        max(case when in_places then 1 else 0 end) as has_places,
        max(case when in_manual then 1 else 0 end) as has_manual
    from {{ ref('bridge_venue_sport') }}
    group by 1
),

manual_ev as (
    select
        mm.effective_venue_id as venue_id,
        max(case m.confirmation_level when 'visited' then 25 when 'official' then 20 else 8 end) as evidence_pts,
        max(m.confirmed_on) as newest_confirmed
    from {{ ref('stg_manual_venues') }} m
    join {{ ref('int_manual_venue_match') }} mm on mm.venue_key = m.venue_key
    group by 1
),

action_ev as (
    select venue_id, max(verified_on) as newest_verified
    from {{ ref('mart_venue_actions') }}
    group by 1
),

scored as (
    select
        v.venue_id,
        v.venue_name,
        v.venue_source,
        v.city,
        10 * (coalesce(s.has_osm, 0) + coalesce(s.has_places, 0) + coalesce(s.has_manual, 0))  as sources_pts,
        coalesce(me.evidence_pts, 0)                                                            as evidence_pts,
        case when v.name_source in ('manual', 'places_directory', 'court_name', 'operator') then 10 else 0 end as named_pts,
        (case when v.website is not null and coalesce(v.website_status, '') <> 'dead' then 8 else 0 end
         + case when v.phone is not null then 4 else 0 end
         + case when v.opening_hours is not null then 4 else 0 end
         + case when v.address_line is not null then 4 else 0 end)                              as contact_pts,
        case
            when greatest(me.newest_confirmed, ae.newest_verified) is null then 0
            when greatest(me.newest_confirmed, ae.newest_verified) >= current_date - 35 then 15
            when greatest(me.newest_confirmed, ae.newest_verified) >= current_date - 90 then 8
            else 0
        end                                                                                     as fresh_pts
    from {{ ref('dim_venue') }} v
    left join src s on s.venue_id = v.venue_id
    left join manual_ev me on me.venue_id = v.venue_id
    left join action_ev ae on ae.venue_id = v.venue_id
)

select
    *,
    sources_pts + evidence_pts + named_pts + contact_pts + fresh_pts                            as confidence_score,
    case
        when sources_pts + evidence_pts + named_pts + contact_pts + fresh_pts >= 60 then 'high'
        when sources_pts + evidence_pts + named_pts + contact_pts + fresh_pts >= 30 then 'medium'
        else 'low'
    end                                                                                         as confidence_band,
    'rules_v1'                                                                                  as score_method,
    'inferred'                                                                                  as confirmation
from scored
