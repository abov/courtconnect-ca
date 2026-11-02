-- Fails (returns rows) if a court has no region or falls outside its region's bounding box (a state in the regions var, ADR 0014, 0028):
-- catches bad geocodes and mis-scoped extractions.
select court_id, lat, lon, region
from {{ ref('dim_court') }}
where {{ outside_region_bbox('lat', 'lon', 'region') }}
