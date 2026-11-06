-- INFERRED "may be closed" lead per venue from two outside sources that stopped listing it, never a confirmed closure (ADR 0026).
--   Overture: seeds/overture_gone_places.csv (ingestion/overture_release_diff.py) remembers places in one release and gone from the next.
--   OSM:      seeds/osm_gone_elements.csv (ingestion/osm_snapshot_diff.py) remembers court elements in one extract and gone from the next
--             (deleted, or their sport/leisure tags removed). Neither raw extract keeps history, so the seeds are the only memory.
-- A gone Overture place counts for a venue only when ALL of these hold, so a vanished business record near a park does not flag the park's courts:
--   - the venue carries the same name as the gone place (letters and digits only, 5+ characters) within `place_name_match_radius_m` metres;
--   - the venue has no live Overture place any more;
--   - the place did not come back in the newest release and is not in closed_places (a person already decided those).
-- A gone OSM element counts for a venue only when it sits within `osm_gone_match_radius_m` of the pin, carries a sport the venue lists,
--   has not come back in the newest extract, and the venue has no live OSM court left (a few removed courts at a venue that still has others
--   is a court-count change, not a lost source).
-- no_surviving_source = the venue has no live Overture place AND no live OSM court. Only then does mart_venue_confidence zero the freshness points
--   (unless a dated check is newer than the latest vanishing). A venue that lost one source but keeps the other stays here as a lead and nothing
--   more: its score already drops because sources_pts counts live sources only. Both signals also fire when an element stops matching the
--   filter or is merged into another record, so a person checks (ADR 0019).
{% set radius = var('place_name_match_radius_m') %}
{% set osm_radius = var('osm_gone_match_radius_m') %}
with gone_places as (
    select
        g.place_id,
        g.place_name,
        cast(g.lat as double)                                       as lat,
        cast(g.lon as double)                                       as lon,
        g.last_seen_release,
        g.gone_in_release,
        cast(left(g.gone_in_release, 10) as date)                   as gone_on,
        regexp_replace(lower(g.place_name), '[^a-z0-9]', '', 'g')   as name_key
    from {{ ref('overture_gone_places') }} g
    where g.place_id not in (select place_id from {{ ref('stg_overture_places') }})
      and g.place_id not in (select place_id from {{ ref('closed_places') }})
),

gone_osm as (
    select
        g.element_id,
        g.kind,
        s.sport_id,
        cast(g.lat as double)                                       as lat,
        cast(g.lon as double)                                       as lon,
        g.last_seen_extract,
        g.gone_in_extract,
        cast(g.gone_in_extract as date)                             as gone_on
    from {{ ref('osm_gone_elements') }} g
    cross join unnest(string_split(lower(replace(g.sport, ' ', '')), ';')) as t(tag)   -- the same tag split as bridge_court_sport
    join {{ ref('osm_sport_map') }} m on m.osm_sport_key = t.tag
    join {{ ref('dim_sport') }} s on s.sport_name = m.sport
    where g.element_id not in (select court_id from {{ ref('stg_osm_courts') }})
),

live_sources as (
    select
        venue_id,
        bool_or(in_places) as live_places,
        bool_or(in_osm)    as live_osm
    from {{ ref('bridge_venue_sport') }}
    group by 1
),

place_candidates as (
    select
        v.venue_id,
        g.place_id                                                  as gone_place_id,
        g.place_name                                                as gone_place_name,
        g.last_seen_release,
        g.gone_in_release,
        g.gone_on,
        sqrt(power((v.lat - g.lat) * 110540, 2) + power((v.lon - g.lon) * cos(radians(g.lat)) * 111320, 2)) as distance_m
    from gone_places g
    join {{ ref('dim_venue') }} v
      on abs(v.lat - g.lat) < 0.004 and abs(v.lon - g.lon) < 0.006
     and length(g.name_key) >= 5
     and regexp_replace(lower(v.venue_name), '[^a-z0-9]', '', 'g') = g.name_key
    left join live_sources ls on ls.venue_id = v.venue_id
    where not coalesce(ls.live_places, false)
),

place_hit as (
    select venue_id, gone_place_id, gone_place_name, last_seen_release, gone_in_release, gone_on, round(distance_m) as distance_m
    from (
        select *, row_number() over (partition by venue_id order by gone_on desc, distance_m, gone_place_id) as rn
        from place_candidates
        where distance_m <= {{ radius }}
    ) x
    where rn = 1
),

osm_candidates as (
    select
        v.venue_id,
        g.element_id,
        g.kind,
        g.last_seen_extract,
        g.gone_in_extract,
        g.gone_on,
        sqrt(power((v.lat - g.lat) * 110540, 2) + power((v.lon - g.lon) * cos(radians(g.lat)) * 111320, 2)) as distance_m
    from gone_osm g
    join {{ ref('dim_venue') }} v
      on v.venue_kind = 'courts'
     and abs(v.lat - g.lat) < {{ osm_radius }} / 100000.0 and abs(v.lon - g.lon) < {{ osm_radius }} / 60000.0   -- degrees, wider than the radius; the exact test is below
    join {{ ref('bridge_venue_sport') }} b on b.venue_id = v.venue_id and b.sport_id = g.sport_id
    left join live_sources ls on ls.venue_id = v.venue_id
    where not coalesce(ls.live_osm, false)
),

osm_hit as (
    select
        venue_id,
        gone_osm_elements,
        element_id                                                  as gone_osm_element_id,
        kind                                                        as gone_osm_kind,
        gone_in_extract,
        gone_on,
        distance_m
    from (
        select
            venue_id, element_id, kind, distance_m,
            count(*) over (partition by venue_id)                   as gone_osm_elements,
            max(gone_in_extract) over (partition by venue_id)       as gone_in_extract,
            max(gone_on) over (partition by venue_id)               as gone_on,
            row_number() over (partition by venue_id order by distance_m, element_id) as rn
        from (select distinct * from osm_candidates where distance_m <= {{ osm_radius }})
    ) x
    where rn = 1
),

combined as (
    select
        coalesce(p.venue_id, o.venue_id)                            as venue_id,
        p.venue_id is not null                                      as overture_gone,
        o.venue_id is not null                                      as osm_gone,
        p.gone_place_id, p.gone_place_name, p.last_seen_release, p.gone_in_release,
        o.gone_osm_elements, o.gone_osm_element_id, o.gone_osm_kind, o.gone_in_extract,
        greatest(coalesce(p.gone_on, cast('1900-01-01' as date)), coalesce(o.gone_on, cast('1900-01-01' as date))) as gone_on,
        least(coalesce(p.distance_m, 1e9), coalesce(o.distance_m, 1e9)) as distance_m
    from place_hit p
    full outer join osm_hit o on o.venue_id = p.venue_id
)

select
    c.venue_id,
    case when c.overture_gone and c.osm_gone then 'overture_and_osm_gone'
         when c.overture_gone then 'overture_place_gone'
         else 'osm_courts_gone' end                                 as closure_signal,
    not (coalesce(ls.live_places, false) or coalesce(ls.live_osm, false)) as no_surviving_source,
    c.gone_place_id,
    c.gone_place_name,
    c.last_seen_release,
    c.gone_in_release,
    c.gone_osm_elements,
    c.gone_osm_element_id,
    c.gone_osm_kind,
    c.gone_in_extract,
    c.gone_on,
    round(c.distance_m)                                             as distance_m,
    concat_ws('; ',
        case when c.overture_gone then 'Overture place "' || c.gone_place_name || '" no longer listed since release ' || c.gone_in_release end,
        case when c.osm_gone then cast(c.gone_osm_elements as varchar) || ' OpenStreetMap court element(s) here ('
                                  || case c.gone_osm_kind when 'deleted' then 'deleted' when 'retagged' then 'no longer tagged as a racket court' else 'no longer in the extract' end
                                  || ') since the ' || c.gone_in_extract || ' extract' end
    ) || ' (inferred; may be a data cleanup, not a closure)'        as closure_detail,
    'inferred'                                                      as confirmation
from combined c
left join live_sources ls on ls.venue_id = c.venue_id
