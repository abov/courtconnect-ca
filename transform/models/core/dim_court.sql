select
    court_id,
    court_name,
    lat,
    lon,
    surface_type,
    is_lit,
    access_type,
    is_free,
    operator_name,
    try_cast(courts_count_raw as integer)                     as courts_count,
    osm_leisure_type,
    extracted_at
from {{ ref('stg_osm_courts') }}
