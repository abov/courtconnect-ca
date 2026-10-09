-- One row per OSM element (a single court, or a facility such as a sports centre), tags standardised.
-- Only records whose sport tag maps to a racket sport on the master sheet are kept
-- (e.g. a pitch tagged only 'tetherball' is dropped, see ADR 0004).
with src as (
    select o.*
    from {{ source('raw', 'osm_courts') }} o
    where o.lat is not null and o.lon is not null
      and exists (
          select 1 from {{ ref('osm_sport_map') }} m
          where ';' || lower(replace(o.sport, ' ', '')) || ';' like '%;' || m.osm_sport_key || ';%'
      )
)

select
    osm_type || '/' || cast(osm_id as varchar)                as court_id,
    nullif(trim(name), '')                                    as court_name,
    cast(lat as double)                                       as lat,
    cast(lon as double)                                       as lon,
    ';' || lower(replace(sport, ' ', '')) || ';'              as sport_tag_delimited,

    -- a 'pitch' is one court; everything else is a facility that contains or names courts
    case when leisure = 'pitch' then 'court' else 'facility' end as record_kind,

    -- playing surface, grouped. First match wins, most specific first.
    case
        when lower(coalesce(surface, '')) = ''                                          then 'unknown'
        when lower(surface) like '%sand%'                                               then 'sand'
        when lower(surface) like '%clay%'                                               then 'clay'
        when lower(surface) like '%artificial%' or lower(surface) like '%turf%'         then 'turf'
        when lower(surface) like '%grass%'                                              then 'grass'
        when lower(surface) like '%carpet%'                                             then 'carpet'
        when lower(surface) like '%wood%' or lower(surface) like '%parquet%'            then 'wood'
        when lower(surface) like '%asphalt%' or lower(surface) like '%concrete%'
          or lower(surface) like '%acrylic%' or lower(surface) like '%hard%'
          or lower(surface) like '%paved%' or lower(surface) like '%paving%'
          or lower(surface) like '%tartan%' or lower(surface) like '%rubber%'
          or lower(surface) like '%plastic%'                                            then 'hard'
        else 'other'
    end                                                       as surface_type,

    -- indoor / covered / outdoor
    case
        when lower(coalesce(indoor, '')) = 'yes' or leisure = 'sports_hall'
          or (building is not null and lower(building) <> 'no')                        then 'indoor'
        when lower(coalesce(covered, '')) = 'yes'                                       then 'covered'
        when lower(coalesce(indoor, '')) = 'no'                                         then 'outdoor'
        when leisure = 'pitch'                                                          then 'likely_outdoor'  -- untagged: an assumption, not data
        else 'unknown'
    end                                                       as setting,

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
    nullif(trim(website), '')                                 as website,
    nullif(trim(phone), '')                                   as phone,
    nullif(trim(opening_hours), '')                           as opening_hours,
    nullif(trim(concat_ws(' ', addr_housenumber, addr_street)), '') as address_line,
    nullif(trim(addr_city), '')                               as city,
    extracted_at
from src
