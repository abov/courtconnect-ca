-- The hitting-wall pins that stand at no listed court venue become venues of their own (ADR 0032, venue_kind 'hitting_wall'); a pin
-- int_wall_venue_link ties to a court venue is a feature of that venue instead, so no pin is listed twice. Same columns as
-- int_venue_court so core.dim_venue can union them. A wall says nothing about indoor/outdoor or surface type: unknown, not "outdoor"
-- (the same stance as places_only). Name quality follows the source: a hand-checked report/official row is 'manual', a real OSM name
-- is 'court_name', the generic default takes the name of the park / school it stands in (int_wall_parent; 'enclosing_feature', inferred), else 'unnamed'. Access comes from the wall's own access label, never assumed public.
select
    md5('wall:' || w.wall_key)                                  as venue_id,
    case when coalesce(w.confirmation, '') not in ('reported', 'official') and w.wall_name = 'Handball / wall court' and wp.parent_name is not null
         then wp.parent_name else w.wall_name end               as venue_name,
    case when w.confirmation in ('reported', 'official') then 'manual'
         when w.wall_name <> 'Handball / wall court' then 'court_name'
         when wp.parent_name is not null then 'enclosing_feature'   -- inferred from the park / school the wall stands in
         else 'unnamed' end                                     as name_source,
    case when coalesce(w.confirmation, '') not in ('reported', 'official') and w.wall_name = 'Handball / wall court' then wp.parent_kind end as name_feature_kind,
    'walls'                                                     as venue_source,
    0                                                           as court_records,
    1                                                           as facility_records,
    w.lat,
    w.lon,
    cast(null as varchar)                                       as website,
    cast(null as varchar)                                       as phone,
    cast(null as varchar)                                       as opening_hours,
    cast(null as varchar)                                       as address_line,
    nullif(w.city, '')                                          as city,
    w.region,
    cast(null as varchar)                                       as offerings,
    coalesce(w.is_lit, false)                                   as has_lit_courts,
    coalesce(w.access = 'public', false)                        as is_confirmed_public,
    coalesce(w.free_to_use, false)                              as has_free_courts,
    coalesce(w.access in ('members', 'private'), false)         as is_members_only,
    cast(null as boolean)                                       as has_indoor,
    false                                                       as has_outdoor,
    'unknown'                                                   as indoor_basis,
    false as has_hard, false as has_clay, false as has_grass, false as has_turf, false as has_sand, false as has_indoor_floor,
    cast(null as varchar)                                       as also_listed_as,
    'hitting_wall'                                              as venue_kind,
    cast(null as varchar)                                       as website_status,
    cast(null as varchar)                                       as google_place_id,
    w.reported_on                                               as source_seen_on   -- when the wall was extracted from OSM or reported by a person
from {{ ref('mart_wall_pins') }} w
left join {{ ref('int_wall_parent') }} wp on wp.wall_key = w.wall_key
where w.wall_key not in (select wall_key from {{ ref('int_wall_venue_link') }})
