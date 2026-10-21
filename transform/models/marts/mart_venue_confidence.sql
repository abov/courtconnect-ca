-- Rule-based confidence score per venue (0-100, rules_v2): how well backed up is the fact that this venue exists with these sports.
-- It is a transparent, INFERRED heuristic ("rules_v2"), not a probability: every point comes from a column you can read here.
--   sources   0-30  one source 10, two 20, three 30 (OpenStreetMap, Overture places, hand-added)
--   evidence  0-25  best hand-added confirmation: visited 25, official 20, reported 8
--   named     0-10  a real name (hand-added, Overture, court name or operator), not a guessed or empty one
--   contact   0-20  usable website 8, phone 4, opening hours 4, address 4
--   fresh     0-15  newest dated check (hand-added confirmation or link-out verification): <=35 days 15, <=90 days 8
--   sport penalty 0 to -15 (added in rules_v2): 15 x the weighted share of the venue's directly evidenced sports that rest only on a loose OSM tag (weight 1) or a
--                 business-name word (weight 0.5; a distinctive word like "padel" is usually right) (mart_sport_evidence.needs_review). Derived sports (sport_also_played) are rule outputs and not counted.
-- last_seen_on: newest date any source saw the venue (OSM extract, Overture release, hand-added confirmation, link-out check); the 35-day
--   freshness SLA in `make quality` reads it. Nulls are coalesced to 1900-01-01 first so one missing date never nulls the greatest().
-- confidence_score_v1 keeps the old score so the effect of the penalty stays visible.
-- Bands: high >= 60, medium 30-59, low < 30.
{% set d0 = "cast('1900-01-01' as date)" %}
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

seen as (
    select venue_id, max(cast(extracted_at as date)) as osm_seen_on
    from {{ ref('dim_court') }}
    group by 1
),

place_seen as (
    select venue_id, max(cast(left(release, 10) as date)) as places_seen_on
    from {{ ref('dim_place') }}
    where venue_id is not null
    group by 1
),

action_ev as (
    select venue_id, max(verified_on) as newest_verified
    from {{ ref('mart_venue_actions') }}
    group by 1
),

sport_roll as (
    select
        venue_id,
        sum(case when best_rung < 7 then 1 else 0 end)             as direct_sports,
        sum(case when best_rung = 4 then 1 when best_rung = 6 then 0.5 else 0 end) as review_sports   -- loose tag counts fully, name-only half
    from {{ ref('mart_sport_evidence') }}
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
            when greatest(coalesce(me.newest_confirmed, {{ d0 }}), coalesce(ae.newest_verified, {{ d0 }})) >= current_date - 35 then 15
            when greatest(coalesce(me.newest_confirmed, {{ d0 }}), coalesce(ae.newest_verified, {{ d0 }})) >= current_date - 90 then 8
            else 0
        end                                                                                     as fresh_pts,
        nullif(greatest(coalesce(me.newest_confirmed, {{ d0 }}), coalesce(ae.newest_verified, {{ d0 }}),
                        coalesce(os.osm_seen_on, {{ d0 }}), coalesce(ps.places_seen_on, {{ d0 }})), {{ d0 }}) as last_seen_on,
        coalesce(sr.direct_sports, 0)                                                           as direct_sports,
        coalesce(sr.review_sports, 0)                                                           as review_sports,
        case when coalesce(sr.direct_sports, 0) = 0 then 0
             else cast(round(15.0 * sr.review_sports / sr.direct_sports) as integer) end        as sport_penalty_pts
    from {{ ref('dim_venue') }} v
    left join src s on s.venue_id = v.venue_id
    left join manual_ev me on me.venue_id = v.venue_id
    left join action_ev ae on ae.venue_id = v.venue_id
    left join seen os on os.venue_id = v.venue_id
    left join place_seen ps on ps.venue_id = v.venue_id
    left join sport_roll sr on sr.venue_id = v.venue_id
)

select
    *,
    sources_pts + evidence_pts + named_pts + contact_pts + fresh_pts                            as confidence_score_v1,
    greatest(0, sources_pts + evidence_pts + named_pts + contact_pts + fresh_pts - sport_penalty_pts) as confidence_score,
    case
        when greatest(0, sources_pts + evidence_pts + named_pts + contact_pts + fresh_pts - sport_penalty_pts) >= 60 then 'high'
        when greatest(0, sources_pts + evidence_pts + named_pts + contact_pts + fresh_pts - sport_penalty_pts) >= 30 then 'medium'
        else 'low'
    end                                                                                         as confidence_band,
    'rules_v2'                                                                                  as score_method,
    'inferred'                                                                                  as confirmation
from scored
