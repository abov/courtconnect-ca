-- Recurring social get-togethers (mixers, club nights, open play, social nights): curated in seeds/social_events.csv, one row per SERIES
-- (not per date, so rows do not go stale each week), each with a link to the organizer's own page. CourtConnect takes no signups or payments.
select
    trim(series_key)                                          as series_key,
    md5('social/' || trim(series_key))                        as series_id,
    trim(series_name)                                         as series_name,
    trim(sport)                                               as sport_name,
    lower(trim(kind))                                         as kind,
    trim(organizer)                                           as organizer,
    trim(venue_name)                                          as venue_name,
    trim(city)                                                as city,
    cast(lat as double)                                       as lat,
    cast(lon as double)                                       as lon,
    trim(location_precision)                                  as location_precision,
    trim(schedule)                                            as schedule,
    cast(nullif(trim(last_listed_date), '') as date)          as last_listed_date,
    nullif(trim(skill_level), '')                             as skill_level,
    lower(nullif(trim(audience), ''))                         as audience,
    lower(nullif(trim(age_focus), ''))                        as age_focus,
    cast(nullif(trim(courts), '') as integer)                 as courts,
    nullif(trim(price_info), '')                              as price_info,
    lower(trim(source_kind))                                  as source_kind,
    nullif(trim(info_url), '')                                as info_url,
    nullif(trim(signup_url), '')                              as signup_url,
    nullif(trim(source_note), '')                             as source_note,
    cast(verified_on as date)                                 as verified_on
from {{ ref('social_events') }}
