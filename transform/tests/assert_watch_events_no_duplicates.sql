-- Fails when two watch events overlap in dates and sit within 1 km of each other, so one event listed under two
-- names (an organizer page and a directory) cannot become two pins. Fix: merge the rows into one (keep the organizer's
-- page, note the other listing in source_note). If they really are different events, add the pair to `reviewed`.
with reviewed(a, b) as (
    values
        ('usa-pickleball-nationals-2026', 'usap-collegiate-series-san-diego-2026'),
        ('socal-open-tour-finals-2026', 'socal-ntrp-tour-finals-singles-2026'),
        ('national-40s-hardcourts-2026', 'national-father-son-hardcourts-2026'),
        ('btsm-winter-kickoff-classic-2026', 'btsm-vision-bt10-nov-20-2026'),
        ('btsm-winter-kickoff-classic-2026', 'btsm-vision-bt10-nov-22-2026')
)
select x.event_key as event_a, y.event_key as event_b, 'possible duplicate event (same place, overlapping dates)' as problem
from {{ ref('stg_watch_events') }} x
join {{ ref('stg_watch_events') }} y
  on x.event_key < y.event_key
 and x.start_date <= coalesce(y.end_date, y.start_date)
 and y.start_date <= coalesce(x.end_date, x.start_date)
 and sqrt(power((x.lat - y.lat) * 111.0, 2) + power((x.lon - y.lon) * 111.0 * cos(radians(x.lat)), 2)) < 1.0
where not exists (
    select 1 from reviewed r
    where (r.a = x.event_key and r.b = y.event_key) or (r.a = y.event_key and r.b = x.event_key)
)
