-- Recurring social get-togethers to join, grouped by sport and city in the app. A discovery list: every row links out to the organizer.
-- `is_current` is as of the build date; the map app recomputes it in the browser so a stale deploy still hides ended series.
select
    e.series_id,
    e.series_name,
    e.sport_name,
    e.kind,
    e.organizer,
    e.venue_name,
    e.city,
    e.lat,
    e.lon,
    e.location_precision,
    e.schedule,
    e.last_listed_date,
    e.skill_level,
    e.audience,
    e.age_focus,
    e.courts,
    e.price_info,
    e.source_kind,
    e.info_url,
    e.signup_url,
    e.source_note,
    e.verified_on,
    (e.last_listed_date is null or e.last_listed_date >= current_date)   as is_current
from {{ ref('stg_social_events') }} e
join {{ ref('dim_sport') }} s on s.sport_name = e.sport_name
