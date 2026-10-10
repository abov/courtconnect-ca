-- Events to go and watch, soonest first. A discovery list: every row links out to the organizer.
-- `is_upcoming` is as of the build date; the map app recomputes it in the browser so a stale deploy still hides past events.
select
    e.event_id,
    e.event_name,
    e.sport_name,
    e.level,
    e.watch_format,
    e.venue_name,
    e.city,
    e.lat,
    e.lon,
    e.location_precision,
    e.start_date,
    e.end_date,
    e.date_status,
    e.ticket_info,
    e.info_url,
    e.tickets_url,
    e.source_note,
    e.verified_on,
    (e.end_date is null or e.end_date >= current_date)        as is_upcoming
from {{ ref('stg_watch_events') }} e
join {{ ref('dim_sport') }} s on s.sport_name = e.sport_name
