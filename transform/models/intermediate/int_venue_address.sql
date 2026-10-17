-- One row per venue: the street address to show and where it came from (docs/ml_plan.md, address fill).
--   address_source 'osm'              : address tagged on the OSM court itself (kept as is)
--   address_source 'overture_place'   : the Overture place record's address (kept as is)
--   address_source 'overture_nearest' : INFERRED, the nearest Overture address point within `address_fill_radius_m` of the pin
--   address_source 'nominatim'        : INFERRED, tier 3: OSM's Nominatim reverse geocode of the pin, cached in the nominatim_addresses
--                                       seed (ingestion/reverse_geocode_blanks.py); only a house number + street within 150 m is used,
--                                       and only for non-home pins that tiers 1-2 left blank
-- A venue that already has an address is never overwritten. Privacy rule (owner, 2026-10-16): home-like pins get a city,
-- never a street (`address_withheld` counts what was held back).
--   home signals: OSM building = house / detached / residential / semidetached_house / bungalow on the court, or an unnamed
--   venue with no court marked public (an unnamed private court, or one nobody tagged, in a residential area: unclear = fail safe).
--   exceptions (full address): building = apartments / dormitory, or an apartment / villas / condos / townhomes / residences /
--   HOA / community / clubhouse name.
{% set radius = var('address_fill_radius_m') %}
{% set cell = 0.004 %}

with v as (
    select venue_id, venue_name, name_source, lat, lon, address_line, city
    from {{ ref('dim_venue') }}
),

court_flags as (
    select
        c.venue_id,
        max(case when lower(coalesce(s.building, '')) in ('house', 'detached', 'residential', 'semidetached_house', 'bungalow') then 1 else 0 end) = 1 as has_home_building,
        max(case when lower(coalesce(s.building, '')) in ('apartments', 'dormitory') then 1 else 0 end) = 1 as has_apartment_building,
        max(case when c.access_type = 'public' then 1 else 0 end) = 1                                       as has_public_court,
        max(case when c.address_line is not null then 1 else 0 end) = 1                                     as court_has_address
    from {{ ref('dim_court') }} c
    join {{ ref('stg_osm_courts') }} s on s.court_id = c.court_id
    group by c.venue_id
),

flags as (
    select
        v.venue_id,
        case
            when coalesce(f.has_apartment_building, false) then false
            when regexp_matches(lower(coalesce(v.venue_name, '')), 'apartment|villas|condo|townhom|residences|hoa|community|clubhouse') then false
            when coalesce(f.has_home_building, false) then true
            when v.name_source = 'unnamed' and not coalesce(f.has_public_court, false) then true
            else false
        end as is_home_like
    from v
    left join court_flags f on f.venue_id = v.venue_id
),

-- nearest address point: grid join (own cell + 8 neighbours, an equi-join), flat-earth distance as in int_court_pairs
venue_cells as (
    select venue_id, lat, lon,
           cast(floor(lat / {{ cell }}) as bigint) as cy,
           cast(floor(lon / {{ cell }}) as bigint) as cx
    from v
    where address_line is null and lat is not null and lon is not null
),

offsets as (
    select -1 as d union all select 0 union all select 1
),

probe as (
    select a.venue_id, a.lat, a.lon, a.cy + dy.d as ny, a.cx + dx.d as nx
    from venue_cells a
    cross join offsets dy
    cross join offsets dx
),

address_cells as (
    select address_id, address_line, city, lat, lon,
           cast(floor(lat / {{ cell }}) as bigint) as cy,
           cast(floor(lon / {{ cell }}) as bigint) as cx
    from {{ ref('stg_overture_addresses') }}
),

candidates as (
    select
        p.venue_id, b.address_id, b.address_line, b.city,
        sqrt(
              power((p.lat - b.lat) * 110540, 2)
            + power((p.lon - b.lon) * cos(radians(p.lat)) * 111320, 2)
        ) as distance_m
    from probe p
    join address_cells b
        on b.cy = p.ny
       and b.cx = p.nx
),

nearest as (
    select venue_id, address_line, city, distance_m
    from (
        select *, row_number() over (partition by venue_id order by distance_m, address_id) as rn
        from candidates
        where distance_m <= {{ radius }}
    ) x
    where rn = 1
),

-- a cached row counts only while the pin is still where it was queried (venue_id can shift when pins merge or split)
nominatim as (
    select m.venue_id, m.address_line, m.city, cast(m.distance_m as integer) as distance_m
    from {{ ref('nominatim_addresses') }} m
    join v on v.venue_id = m.venue_id
    where m.status = 'address' and m.address_line is not null
      and abs(v.lat - cast(m.lat as double)) < 0.0003 and abs(v.lon - cast(m.lon as double)) < 0.0003
)

select
    v.venue_id,
    fl.is_home_like,
    case
        when v.address_line is not null then v.address_line
        when not fl.is_home_like then coalesce(n.address_line, nm.address_line)
    end                                                       as address_line,
    case
        when v.address_line is not null and coalesce(cf.court_has_address, false) then 'osm'
        when v.address_line is not null                                           then 'overture_place'
        when not fl.is_home_like and n.address_line is not null                  then 'overture_nearest'
        when not fl.is_home_like and nm.address_line is not null                 then 'nominatim'
    end                                                       as address_source,
    case when v.address_line is null and not fl.is_home_like and n.address_line is not null
         then cast(round(n.distance_m) as integer)
         when v.address_line is null and not fl.is_home_like and nm.address_line is not null
         then nm.distance_m end                               as address_distance_m,
    -- city for a pin with none (city is not sensitive: it never names a street); used by the map's location search
    coalesce(v.city, n.city, nm.city)                         as city,
    (v.address_line is null and fl.is_home_like and n.address_line is not null) as address_withheld
from v
join flags fl on fl.venue_id = v.venue_id
left join court_flags cf on cf.venue_id = v.venue_id
left join nearest n on n.venue_id = v.venue_id
left join nominatim nm on nm.venue_id = v.venue_id
