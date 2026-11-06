-- INFERRED "may be closed" signal from Overture release-to-release diffs (ADR 0026, ingestion/overture_release_diff.py), never a confirmed closure.
-- seeds/overture_gone_places.csv remembers Overture places that were in one release and gone from the next (the raw extract is overwritten each refresh).
-- A gone place flags a venue only when ALL of these hold, so a vanished business record near a park does not flag the park's courts:
--   - the venue carries the same name as the gone place (letters and digits only, 5+ characters) within `place_name_match_radius_m` metres;
--   - the venue has no live Overture place any more (OSM or a hand-added row still lists it, nothing in Overture does);
--   - the place did not come back in the newest release and is not in closed_places (a person already decided those).
-- mart_venue_confidence zeroes freshness points for a flagged venue unless a dated check (hand-added confirmation, link-out verification) is newer than the release the place vanished in.
-- Overture `gone` also fires when a place stops matching the racket filter or is merged into another record, so this is a lead for a person to check.
{% set radius = var('place_name_match_radius_m') %}
with gone as (
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

live as (
    select distinct venue_id from {{ ref('bridge_venue_sport') }} where in_places
),

candidates as (
    select
        v.venue_id,
        g.place_id                                                  as gone_place_id,
        g.place_name                                                as gone_place_name,
        g.last_seen_release,
        g.gone_in_release,
        g.gone_on,
        sqrt(power((v.lat - g.lat) * 110540, 2) + power((v.lon - g.lon) * cos(radians(g.lat)) * 111320, 2)) as distance_m
    from gone g
    join {{ ref('dim_venue') }} v
      on abs(v.lat - g.lat) < 0.004 and abs(v.lon - g.lon) < 0.006
     and length(g.name_key) >= 5
     and regexp_replace(lower(v.venue_name), '[^a-z0-9]', '', 'g') = g.name_key
    where v.venue_id not in (select venue_id from live)
)

select
    venue_id,
    'overture_place_gone'                                           as closure_signal,
    gone_place_id,
    gone_place_name,
    last_seen_release,
    gone_in_release,
    gone_on,
    round(distance_m)                                               as distance_m,
    'inferred'                                                      as confirmation
from (
    select *, row_number() over (partition by venue_id order by gone_on desc, distance_m, gone_place_id) as rn
    from candidates
    where distance_m <= {{ radius }}
) x
where rn = 1
