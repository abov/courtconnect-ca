-- The ADR 0013 usage metrics, one row per week (Monday start), so the numbers mean the same thing every time.
--   north star   : linkouts                (event `linkout`: the player went to the provider)
--   engagement   : venue_opens_per_view    = venue-open / page views
--   usefulness   : linkout_rate            = linkout / venue-open
--   contribution : contributions           = suggest-change + osm-edit + report-form
-- Counts are approximate and directional only (ad blockers and Do Not Track hide visits; no user-level funnels).
-- Sparse weeks have no row; a week with page views but no events still appears. Rates are null when the divisor is 0.
with views as (
    select date_trunc('week', day)::date as week_start, sum(page_views) as page_views
    from {{ ref('stg_usage_daily') }}
    group by 1
),

ev as (
    select
        date_trunc('week', day)::date                                                          as week_start,
        sum(event_count) filter (where event = 'venue-open')                                   as venue_opens,
        sum(event_count) filter (where event = 'linkout')                                      as linkouts,
        sum(event_count) filter (where event in ('suggest-change', 'osm-edit', 'report-form')) as contributions
    from {{ ref('stg_usage_events') }}
    group by 1
)

select
    coalesce(v.week_start, e.week_start)             as week_start,
    coalesce(v.page_views, 0)                        as page_views,
    coalesce(e.venue_opens, 0)                       as venue_opens,
    coalesce(e.linkouts, 0)                          as linkouts,
    coalesce(e.contributions, 0)                     as contributions,
    round(coalesce(e.venue_opens, 0) * 1.0 / nullif(v.page_views, 0), 3) as venue_opens_per_view,
    round(coalesce(e.linkouts, 0) * 1.0 / nullif(e.venue_opens, 0), 3)   as linkout_rate
from views v
full outer join ev e on v.week_start = e.week_start
order by week_start
