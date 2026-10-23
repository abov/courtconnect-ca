-- To-do list for sleuthing: every lead that still needs work, oldest first. Closed leads (confirmed / resolved / rejected) drop off.
select
    lead_id,
    lead_name,
    city,
    sport_name,
    claim,
    source_type,
    source_url,
    status,
    next_step,
    noted_on,
    notes,
    directories_seen
from {{ ref('stg_venue_leads') }}
where status in ('new', 'needs_location', 'needs_visit')
