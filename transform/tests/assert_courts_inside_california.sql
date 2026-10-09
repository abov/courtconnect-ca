-- Fails (returns rows) if any court falls outside California's bounding box:
-- catches bad geocodes and mis-scoped extractions.
select court_id, lat, lon
from {{ ref('dim_court') }}
where lat not between 32.5 and 42.1
   or lon not between -124.5 and -114.1
