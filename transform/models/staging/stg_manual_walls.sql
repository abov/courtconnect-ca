-- Hitting walls for solo practice (one-wall, three-wall, backboards): curated in seeds/manual_walls.csv. A wall is not a court,
-- so it lives apart from venues. Blank is_lit / free_to_use means unknown (never read as no).
select
    trim(wall_key)                                            as wall_key,
    md5('wall/' || trim(wall_key))                            as wall_id,
    trim(wall_name)                                           as wall_name,
    trim(city)                                                as city,
    cast(lat as double)                                       as lat,
    cast(lon as double)                                       as lon,
    trim(location_precision)                                  as location_precision,
    lower(trim(wall_type))                                    as wall_type,
    trim(sports_suited)                                       as sports_suited,
    nullif(trim(near_venue_name), '')                         as near_venue_name,
    nullif(lower(trim(surface)), '')                          as surface,
    case lower(trim(is_lit)) when 'yes' then true when 'no' then false end            as is_lit,
    case lower(trim(free_to_use)) when 'yes' then true when 'no' then false end      as free_to_use,
    nullif(lower(trim(access)), '')                           as access,
    lower(trim(confirmation))                                 as confirmation,
    cast(reported_on as date)                                 as reported_on,
    nullif(trim(evidence), '')                                as evidence,
    upper(trim(region))                                       as region      -- CA / NV
from {{ ref('manual_walls') }}
