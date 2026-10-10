-- The sleuthing backlog: things reported but not yet located or confirmed (seeds/venue_leads.csv).
-- A lead is NOT shown on the map. When it is confirmed it becomes a row in manual_venues (with a confirmation level) and
-- its status here becomes 'confirmed' or 'resolved'.
select
    trim(lead_id)                                             as lead_id,
    trim(name)                                                as lead_name,
    nullif(trim(city), '')                                    as city,
    trim(sport)                                               as sport_name,
    nullif(trim(claim), '')                                   as claim,
    lower(trim(source_type))                                  as source_type,
    nullif(trim(source_url), '')                              as source_url,
    lower(trim(status))                                       as status,
    nullif(trim(next_step), '')                               as next_step,
    cast(noted_on as date)                                    as noted_on,
    nullif(trim(notes), '')                                   as notes
from {{ ref('venue_leads') }}
