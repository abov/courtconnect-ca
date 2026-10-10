-- What you can DO at a venue, with the provider's own link: join a league, take a clinic, find open play, book a lesson.
-- Link-outs only (ADR 0006): CourtConnect books nothing. Each row says which platform runs it, where to go, and how we know.
-- A row points at a hand-added venue (venue_ref_type 'manual', venue_ref = venue_key) or an Overture place ('place', venue_ref = place_id).
select
    trim(a.action_key)                                        as action_key,
    coalesce(mm.effective_venue_id, p.venue_id)               as venue_id,
    lower(trim(a.action_type))                                as action_type,
    trim(a.title)                                             as title,
    lower(trim(a.provider))                                   as provider,
    trim(a.url)                                               as url,
    nullif(trim(a.price_info), '')                            as price_info,
    cast(nullif(trim(a.start_date), '') as date)              as start_date,
    cast(nullif(trim(a.end_date), '') as date)                as end_date,
    nullif(trim(a.evidence), '')                              as evidence,
    cast(a.verified_on as date)                               as verified_on
from {{ ref('venue_actions') }} a
left join {{ ref('int_manual_venue_match') }} mm on lower(trim(a.venue_ref_type)) = 'manual' and mm.venue_key = trim(a.venue_ref)
left join {{ ref('dim_place') }} p on lower(trim(a.venue_ref_type)) = 'place' and p.place_id = trim(a.venue_ref)
