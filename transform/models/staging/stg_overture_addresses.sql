-- Overture Maps address points that sit near a map pin (CDLA-Permissive; NOTICE.md). Not the whole state: the extract keeps
-- only the points within ~440 m of a pin (ingestion/extract_overture_addresses.py). Used to fill pins with no street address.
select
    address_id,
    trim(concat_ws(' ', cast(house_number as varchar), cast(street as varchar))) as address_line,
    nullif(trim(cast(city as varchar)), '')                   as city,
    nullif(trim(cast(postcode as varchar)), '')               as postcode,
    cast(lat as double)                                       as lat,
    cast(lon as double)                                       as lon
from {{ source('raw', 'overture_addresses') }}
where lat is not null and lon is not null
  and nullif(trim(cast(house_number as varchar)), '') is not null
  and nullif(trim(cast(street as varchar)), '') is not null
