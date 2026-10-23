-- Hitting walls mapped in OpenStreetMap (handball and wall courts, tennis backboards and practice walls). The wall type is not
-- known from the tags: sport=american_handball is used for 1-wall, 3-wall and 4-wall courts alike, and OSM has no wall-count tag.
-- Owner decision 2026-10-22 (replaces 2026-10-14, when every one was called three-wall): with no public page or visit report
-- either way, a handball / wallball court is assumed ONE-wall (the app labels it "assumed"). A three_wall type needs a reported
-- or official source in manual_walls.csv. Backboard stays 'backboard' when the name or tags say so.
-- Blank lit / fee means unknown (never read as no). The pin is the mapped feature, so the location is exact.
select
    'osm-' || osm_type || '-' || cast(cast(osm_id as bigint) as varchar)                      as wall_key,
    md5('wall/osm-' || osm_type || '-' || cast(cast(osm_id as bigint) as varchar))            as wall_id,
    coalesce(nullif(trim(name), ''), 'Handball / wall court')                                 as wall_name,
    coalesce(nullif(trim(addr_city), ''), '')                                                 as city,
    cast(lat as double)                                                                       as lat,
    cast(lon as double)                                                                       as lon,
    'exact: mapped feature in OpenStreetMap'                                                  as location_precision,
    case when lower(coalesce(name, '')) like '%backboard%' or lower(coalesce(name, '')) like '%practice wall%'
              or lower(coalesce(name, '')) like '%hitting wall%' or tennis = 'hitting_wall' or leisure = 'practice_wall'
         then 'backboard'
         when lower(sport) like '%handball%' or lower(sport) like '%wallball%' then 'one_wall'
         else 'other' end                                                    as wall_type,
    concat_ws(';',
        case when lower(sport) like '%handball%' or lower(sport) like '%wallball%' then 'Handball' end,
        case when lower(sport) like '%racquetball%' then 'Racquetball' end,
        case when lower(sport) like '%tennis%' or tennis = 'hitting_wall' then 'Tennis' end,
        case when lower(sport) like '%squash%' then 'Squash' end,
        case when lower(sport) like '%pickleball%' then 'Pickleball' end)                     as sports_suited,
    cast(null as varchar)                                                                     as near_venue_name,
    nullif(lower(trim(surface)), '')                                                          as surface,
    case lower(trim(lit)) when 'yes' then true when 'no' then false end                       as is_lit,
    case lower(trim(fee)) when 'no' then true when 'yes' then false end                       as free_to_use,
    -- same vocabulary as stg_osm_courts.access_type; anything unrecognised stays NULL (not known)
    case lower(trim(access))
        when 'yes' then 'public'
        when 'public' then 'public'
        when 'permissive' then 'public'
        when 'customers' then 'customers'
        when 'private' then 'private'
        when 'no' then 'private'
        when 'members' then 'members'
    end                                                                                       as access,
    'tagged'                                                                                  as confirmation,
    cast(extracted_at as date)                                                                as reported_on,
    'OpenStreetMap ' || osm_type || ' ' || cast(cast(osm_id as bigint) as varchar) || ', tagged sport=' || coalesce(sport, 'n/a')
        || '. Only the tags are known: the number of walls (assumed one), condition and whether it is open to the public were not checked.'      as evidence,
    {{ region_code('region') }}                                                               as region
from {{ source('raw', 'osm_walls') }}
