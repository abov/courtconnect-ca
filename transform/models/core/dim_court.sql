select
    c.court_id,
    k.cluster_label                                           as venue_key,
    md5(k.cluster_label)                                      as venue_id,
    c.record_kind,
    c.court_name,
    c.lat,
    c.lon,
    c.surface_type,
    c.setting,
    c.is_lit,
    c.access_type,
    c.is_free,
    c.operator_name,
    try_cast(c.courts_count_raw as integer)                   as courts_count,
    c.osm_leisure_type,
    c.website,
    c.phone,
    c.opening_hours,
    c.address_line,
    c.city,
    p.parent_name,
    p.parent_kind,
    p.parent_area,
    c.extracted_at
from {{ ref('stg_osm_courts') }} c
join {{ ref('int_court_clusters') }} k on k.court_id = c.court_id
left join {{ ref('int_court_parent') }} p on p.court_id = c.court_id
