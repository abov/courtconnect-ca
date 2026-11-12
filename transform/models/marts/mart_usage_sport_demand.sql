-- ADR 0013 "demand by sport": how often each sport was picked on the map next to what we have for it. Directional only (docs/goat_analysis.md).
-- Picks come from `sport-pick` events (detail = the sport as shown in the app); matched to the master sheet by lower-cased name.
-- Picks whose name matches no sport (a renamed sport, a filter like "All") are kept with venues_found null so nothing is silently dropped.
with picks as (
    select detail as picked_name, lower(trim(detail)) as pick_key, sum(event_count) as picks, count(distinct day) as days_picked
    from {{ ref('stg_usage_events') }}
    where event = 'sport-pick' and detail <> ''
    group by 1, 2
),

gaps as (
    select lower(trim(sport_name)) as pick_key, sport_name, venues_found, courts_found, coverage_status
    from {{ ref('mart_sport_gaps') }}
)

select
    coalesce(g.sport_name, p.picked_name)  as sport_name,
    p.picks,
    p.days_picked,
    g.venues_found,
    g.courts_found,
    g.coverage_status,
    p.picks * 1.0 / sum(p.picks) over ()   as pick_share
from picks p
left join gaps g on p.pick_key = g.pick_key
order by p.picks desc, sport_name
