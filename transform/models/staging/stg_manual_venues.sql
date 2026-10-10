-- Venues no data source knows about, added by hand (transform/seeds/manual_venues.csv).
-- One row per (venue, sport). `evidence` says how well each entry is backed up; `access` is public / unknown / private.
select
    md5('manual/' || trim(venue_key))                         as venue_id,
    trim(venue_key)                                           as venue_key,
    trim(venue_name)                                          as venue_name,
    trim(sport)                                               as sport_name,
    nullif(trim(city), '')                                    as city,
    cast(lat as double)                                       as lat,
    cast(lon as double)                                       as lon,
    nullif(trim(location_precision), '')                      as location_precision,
    nullif(trim(website), '')                                 as website,
    lower(trim(surface_type))                                 as surface_type,
    lower(trim(setting))                                      as setting,
    nullif(trim(offerings), '')                               as offerings,
    try_cast(nullif(trim(courts), '') as integer)             as courts_count,
    lower(coalesce(nullif(trim(access), ''), 'unknown'))      as access_type,
    nullif(trim(rules), '')                                   as rules_note,
    nullif(trim(evidence), '')                                as evidence
from {{ ref('manual_venues') }}
