-- Racket-related places from Overture Maps (businesses, clubs, venues). Licensed CDLA-Permissive-2.0 / Apache-2.0 / CC0,
-- so unlike Google Places content it can be stored and republished with attribution (NOTICE.md).
select
    place_id,
    trim(name)                                                as place_name,
    {{ normalize_name('name') }}                              as name_norm,
    category,
    top_category,
    sub_category,
    cast(lat as double)                                       as lat,
    cast(lon as double)                                       as lon,
    cast(confidence as double)                                as confidence,
    nullif(trim(website), '')                                 as website,
    nullif(trim(phone), '')                                   as phone,
    nullif(trim(address), '')                                 as address_line,
    nullif(trim(city), '')                                    as city,
    nullif(trim(postcode), '')                                as postcode,
    license,
    source_dataset,
    release
from {{ source('raw', 'overture_places') }}
where lat is not null and lon is not null
  and coalesce(lower(operating_status), 'open') not in ('closed', 'permanently_closed')
