-- One row per hitting-wall map pin (what the app exports). Walls grouped in int_wall_clusters share a pin at their
-- centre; `wall_count` says how many walls stand there. Flags that differ inside a group become NULL (unknown), never a
-- guess. The name is a real OSM name when any wall in the group has one, else the generic default.
with walls as (
    select w.*, c.wall_group
    from {{ ref('dim_wall') }} w
    join {{ ref('int_wall_clusters') }} c on c.wall_key = w.wall_key
),

grouped as (
    select
        wall_group,
        count(*)                                                                                   as wall_count,
        coalesce(min(case when wall_name <> 'Handball / wall court' then wall_name end), min(wall_name)) as wall_name,
        coalesce(min(nullif(city, '')), '')                                                        as city,
        min(region)                                                                                as region,
        avg(lat)                                                                                   as lat,
        avg(lon)                                                                                   as lon,
        min(location_precision)                                                                    as location_precision,
        min(wall_type)                                                                             as wall_type,
        max(case when sports_suited like '%Handball%' then 1 else 0 end)                           as s_handball,
        max(case when sports_suited like '%Racquetball%' then 1 else 0 end)                        as s_racquetball,
        max(case when sports_suited like '%Tennis%' then 1 else 0 end)                             as s_tennis,
        max(case when sports_suited like '%Squash%' then 1 else 0 end)                             as s_squash,
        max(case when sports_suited like '%Pickleball%' then 1 else 0 end)                         as s_pickleball,
        min(sports_suited)                                                                         as first_sports,
        min(near_venue_name)                                                                       as near_venue_name,
        case when count(distinct surface) = 1 and count(surface) = count(*) then min(surface) end  as surface,
        case when count(is_lit) = count(*) then
             case when min(case when is_lit then 1 else 0 end) = 1 then true
                  when max(case when is_lit then 1 else 0 end) = 0 then false end end              as is_lit,
        case when count(free_to_use) = count(*) then
             case when min(case when free_to_use then 1 else 0 end) = 1 then true
                  when max(case when free_to_use then 1 else 0 end) = 0 then false end end         as free_to_use,
        case when count(distinct access) = 1 and count(access) = count(*) then min(access) end     as access,
        min(confirmation)                                                                          as confirmation,
        max(reported_on)                                                                           as reported_on,
        min(evidence)                                                                              as first_evidence
    from walls
    group by wall_group
)

select
    wall_group                                                                                     as wall_key,
    wall_count,
    wall_name,
    city,
    region,
    lat,
    lon,
    location_precision,
    wall_type,
    -- one wall keeps its own list as written; a group gets the union, in the same order stg_osm_walls writes it
    case when wall_count = 1 then first_sports
         else concat_ws(';',
              case when s_handball = 1 then 'Handball' end,
              case when s_racquetball = 1 then 'Racquetball' end,
              case when s_tennis = 1 then 'Tennis' end,
              case when s_squash = 1 then 'Squash' end,
              case when s_pickleball = 1 then 'Pickleball' end) end                                as sports_suited,
    near_venue_name,
    surface,
    is_lit,
    free_to_use,
    access,
    confirmation,
    reported_on,
    case when wall_count = 1 then first_evidence
         else cast(wall_count as varchar) || ' walls mapped side by side in OpenStreetMap (within '
              || '{{ var("wall_group_radius_m") }} m); the pin is their centre. One of them: ' || first_evidence end as evidence
from grouped
