-- Fails (returns rows) if a court has no region or falls outside its region's bounding box (CA or NV, ADR 0014):
-- catches bad geocodes and mis-scoped extractions.
select court_id, lat, lon, region
from {{ ref('dim_court') }}
where {{ outside_region_bbox('lat', 'lon', 'region') }}
