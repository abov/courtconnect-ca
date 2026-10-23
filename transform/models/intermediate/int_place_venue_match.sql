-- Link each Overture place to the OSM venue it is part of. Three rules, strongest first (a place takes the first rule that fits):
--   distance       nearest OSM court/facility within `place_match_radius_m` metres
--   same_name      within `place_name_match_radius_m` when place and an OSM court carry the same name
--                  (Overture and OSM often put the same club's pin a little apart)
--   facility_name  within `place_facility_match_radius_m` when the place is named after the court's park/school/centre
--                  ("Memorial Park Tennis Courts" for courts mapped inside Memorial Park), or place and court/park share a street address.
--                  Added after the gold set found 17 of 19 checked unmatched places were such misses (docs/gold_set_plan.md).
--                  A bare city name inside a longer parent name ("Atascadero Pickleball Club" vs "Atascadero Unified School District") never counts (an equal name, "Tustin Sports Park", still does):
--                  radius 300 m (was 200) after the third gold slice, which showed this guard is needed there.
--   inside_facility  a place the three rules above leave unmatched joins a court's park/school/centre when its pin lies inside that
--                  feature's (small) bounding box, the nearest of that feature's courts is within `place_inside_match_radius_m`, the place is a
--                  racquet-sport lesson/court record (not a club, resort, league or gym: those are often a different business next door,
--                  e.g. Walnut Creek Racquet Club beside Heather Farm Park) and its name does not say another sport. Gold set, third slice.
-- Same grid-bucket trick as int_court_pairs, so it scales statewide.
{% set radius = var('place_match_radius_m') %}
{% set name_radius = var('place_name_match_radius_m') %}
{% set facility_radius = var('place_facility_match_radius_m') %}
{% set inside_radius = var('place_inside_match_radius_m') %}
{% set inside_max_area = var('place_inside_max_bbox_deg2') %}
{% set not_inside_words = ['club','resort','country','association','society','league','federation','table','ping','badminton','squash','racquetball','handball'] %}
{% set inside_categories = ['tennis_court','fitness_trainer','sports_and_recreation','sport_or_recreation_club','pickleball_court','park'] %}
{% set cell = name_radius / 80000.0 %}

with places as (
    select place_id, lower(trim(place_name)) as name_key, lower(place_name) as name_lc, category, {{ facility_key(normalize_name('place_name')) }} as fac_key,
           trim({{ normalize_name('city') }}) as city_key,
           case when address_line is not null and substr(trim(address_line), 1, 1) between '0' and '9'
                then {{ address_key('address_line') }} end as addr_key,
           lat, lon,
           cast(floor(lat / {{ cell }}) as bigint) as cy,
           cast(floor(lon / {{ cell }}) as bigint) as cx
    from {{ ref('stg_overture_places') }}
),

courts as (
    select c.court_id, lower(c.court_name) as name_key, c.lat, c.lon, md5(k.cluster_label) as venue_id, cp.parent_id, cp.parent_kind,
           -- golf courses / hotels have big irregular bounding boxes that swallow neighbours' courts (int_court_parent), so their names never count
           case when cp.parent_kind <> 'resort_or_other' then {{ facility_key(normalize_name('cp.parent_name')) }} end as parent_key,
           {{ address_key('c.address_line') }} as court_addr_key,
           {{ address_key('pr.address_line') }} as parent_addr_key,
           cast(floor(c.lat / {{ cell }}) as bigint) as cy,
           cast(floor(c.lon / {{ cell }}) as bigint) as cx
    from {{ ref('stg_osm_courts') }} c
    join {{ ref('int_court_clusters') }} k on k.court_id = c.court_id
    left join {{ ref('int_court_parent') }} cp on cp.court_id = c.court_id
    left join {{ ref('stg_osm_parents') }} pr on pr.parent_id = cp.parent_id
),

offsets as (
    select -1 as d union all select 0 union all select 1
),

candidates as (
    select
        p.place_id, c.venue_id, (p.name_key = c.name_key) as same_name,
        -- the distinctive part of the place name is, or contains, the park/school/centre name (or the reverse); 5+ characters so a stub never matches
        (length(trim(p.fac_key)) >= 5 and length(trim(c.parent_key)) >= 5 and not (trim(p.fac_key) = p.city_key and trim(c.parent_key) <> trim(p.fac_key))
         and (p.fac_key like '%' || c.parent_key || '%' or c.parent_key like '%' || p.fac_key || '%')) as facility_name,
        (p.addr_key is not null and length(p.addr_key) > 8
         and (p.addr_key = c.court_addr_key or p.addr_key = c.parent_addr_key)) as same_address,
        sqrt(power((p.lat - c.lat) * 110540, 2)
           + power((p.lon - c.lon) * cos(radians(p.lat)) * 111320, 2)) as distance_m
    from places p
    cross join offsets dy
    cross join offsets dx
    join courts c on c.cy = p.cy + dy.d and c.cx = p.cx + dx.d
),

ruled as (
    select place_id, venue_id, distance_m,
           case when distance_m <= {{ radius }} then 'distance'
                when same_name and distance_m <= {{ name_radius }} then 'same_name'
                when (facility_name or same_address) and distance_m <= {{ facility_radius }} then 'facility_name'
           end as match_rule
    from candidates
),

in_footprint as (
    select p.place_id, c.venue_id,
           sqrt(power((p.lat - c.lat) * 110540, 2) + power((p.lon - c.lon) * cos(radians(p.lat)) * 111320, 2)) as distance_m
    from places p
    join {{ ref('stg_osm_parents') }} par
      on p.lat between par.minlat and par.maxlat and p.lon between par.minlon and par.maxlon
    join courts c on c.parent_id = par.parent_id
    where par.kind_group in ('school', 'park', 'community', 'sports_facility')
      and par.bbox_area_deg2 <= {{ inside_max_area }}
      -- a human 'reject' in place_sport_overrides means the page names no courts or facility (ADR 0016): never place it by footprint
      and not exists (select 1 from {{ ref('place_sport_overrides') }} o where o.place_id = p.place_id and lower(trim(o.verdict)) = 'reject')
      and p.category in ({% for c in inside_categories %}'{{ c }}'{{ ',' if not loop.last }}{% endfor %})
      {% for w in not_inside_words %}and p.name_lc not like '%{{ w }}%'
      {% endfor %}
),

all_ruled as (
    select place_id, venue_id, distance_m, match_rule from ruled where match_rule is not null
    union all
    select place_id, venue_id, distance_m, 'inside_facility' from in_footprint where distance_m <= {{ inside_radius }}
)

select place_id, venue_id, distance_m, match_rule
from (
    select *, row_number() over (
        partition by place_id
        order by case match_rule when 'distance' then 1 when 'same_name' then 2 when 'facility_name' then 3 else 4 end, distance_m, venue_id
    ) as rn
    from all_ruled
) x
where rn = 1
