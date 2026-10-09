-- One row per OSM element, with tags standardised.
select
    osm_type || '/' || cast(osm_id as varchar)                as court_id,
    nullif(trim(name), '')                                    as court_name,
    cast(lat as double)                                       as lat,
    cast(lon as double)                                       as lon,
    ';' || lower(replace(sport, ' ', '')) || ';'              as sport_tag_delimited,
    case lower(coalesce(surface, ''))
        when '' then 'unknown'
        when 'asphalt' then 'hard'
        when 'concrete' then 'hard'
        when 'acrylic' then 'hard'
        when 'hard' then 'hard'
        when 'clay' then 'clay'
        when 'grass' then 'grass'
        when 'artificial_turf' then 'turf'
        when 'sand' then 'sand'
        else 'other'
    end                                                       as surface_type,
    lower(coalesce(lit, '')) = 'yes'                          as is_lit,
    case lower(coalesce(access, ''))
        when 'yes' then 'public'
        when 'public' then 'public'
        when 'permissive' then 'public'
        when 'customers' then 'customers'
        when 'private' then 'private'
        when 'members' then 'members'
        else 'unknown'
    end                                                       as access_type,
    case lower(coalesce(fee, '')) when 'no' then true when 'yes' then false end as is_free,
    nullif(trim(operator), '')                                as operator_name,
    nullif(cast(courts as varchar), '')                       as courts_count_raw,
    leisure                                                   as osm_leisure_type,
    extracted_at
from {{ source('raw', 'osm_courts') }}
where lat is not null and lon is not null
