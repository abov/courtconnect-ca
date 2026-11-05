-- Racket sport vacations: stay-and-play resorts, camps, academies and tours, curated in seeds/racket_vacations.csv.
-- Link-out only (ADR 0007, 0036): `info_url` is the provider's own page; nothing is booked or sold here.
-- `status` = verified (own page or a dated news item, with evidence + verified_on) or lead (stays in the seed, never shown).
select
    trim(vacation_key)                                        as vacation_key,
    md5('vacation/' || trim(vacation_key))                   as vacation_id,
    trim(name)                                                as vacation_name,
    lower(trim(kind))                                         as kind,
    trim(destination)                                         as destination,
    upper(trim(country))                                      as country,
    cast(lat as double)                                       as lat,
    cast(lon as double)                                       as lon,
    trim(sports)                                              as sports,
    lower(trim(who_can_play))                                 as who_can_play,
    nullif(trim(price_note), '')                              as price_note,
    nullif(trim(info_url), '')                                as info_url,
    nullif(trim(evidence), '')                                as evidence,
    cast(verified_on as date)                                 as verified_on,
    lower(trim(status))                                       as status
from {{ ref('racket_vacations') }}
