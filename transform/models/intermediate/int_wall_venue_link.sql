-- Links each hitting-wall map pin to the one venue it stands at, so the venue's popup can say "Hitting walls on site".
-- A wall pin links to at most one venue: the venue whose name equals the pin's `near_venue_name` (within
-- `wall_venue_link_name_radius_m`), else the nearest venue within `wall_venue_link_radius_m`; no match, no link.
-- Only venues the app lists (the ones in bridge_venue_sport) can be linked. The wall stays its own orange pin: this is
-- a pointer, walls do not count as courts and change no venue or sport count.
with venues as (
    select
        v.venue_id,
        lower(trim(v.venue_name))                          as raw_name,
        lower(trim(coalesce(dn.display_name, v.venue_name))) as shown_name,
        v.lat,
        v.lon
    from {{ ref('dim_venue') }} v
    left join {{ ref('int_venue_display_name') }} dn on dn.venue_id = v.venue_id
    where v.venue_id in (select venue_id from {{ ref('bridge_venue_sport') }})
      and v.lat is not null and v.lon is not null
),

candidates as (
    select
        w.wall_key,
        v.venue_id,
        coalesce(lower(trim(w.near_venue_name)) in (v.raw_name, v.shown_name), false) as name_match,
        sqrt(
              power((w.lat - v.lat) * 110540, 2)
            + power((w.lon - v.lon) * cos(radians(w.lat)) * 111320, 2)
        ) as distance_m
    from {{ ref('mart_wall_pins') }} w
    join venues v
        on abs(v.lat - w.lat) < 0.01
       and abs(v.lon - w.lon) < 0.01
),

ranked as (
    select
        *,
        row_number() over (partition by wall_key order by name_match desc, distance_m, venue_id) as rn
    from candidates
    where (name_match and distance_m <= {{ var('wall_venue_link_name_radius_m') }})
       or distance_m <= {{ var('wall_venue_link_radius_m') }}
)

select
    wall_key,
    venue_id,
    case when name_match then 'name' else 'distance' end as link_basis,
    round(distance_m)::integer                           as distance_m
from ranked
where rn = 1
