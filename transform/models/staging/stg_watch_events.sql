-- Matches and tournaments people can go and WATCH (not book): curated in seeds/watch_events.csv, each with a link to the
-- organizer's own page. We never sell or reserve anything; `info_url` / `tickets_url` are link-outs.
select
    trim(event_key)                                           as event_key,
    md5('event/' || trim(event_key))                          as event_id,
    trim(event_name)                                          as event_name,
    trim(sport)                                               as sport_name,
    lower(trim(level))                                        as level,
    lower(trim(watch_format))                                 as watch_format,
    trim(venue_name)                                          as venue_name,
    trim(city)                                                as city,
    cast(lat as double)                                       as lat,
    cast(lon as double)                                       as lon,
    trim(location_precision)                                  as location_precision,
    cast(nullif(trim(start_date), '') as date)                as start_date,
    cast(nullif(trim(end_date), '') as date)                  as end_date,
    lower(trim(date_status))                                  as date_status,
    nullif(trim(ticket_info), '')                             as ticket_info,
    nullif(trim(info_url), '')                                as info_url,
    nullif(trim(tickets_url), '')                             as tickets_url,
    nullif(trim(source_note), '')                             as source_note,
    cast(verified_on as date)                                 as verified_on
from {{ ref('watch_events') }}
