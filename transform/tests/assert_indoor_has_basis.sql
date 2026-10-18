-- has_indoor is only true/false when something backs it (indoor_basis); with no basis it must be null (unknown), never a default false.
select venue_id, has_indoor, indoor_basis
from {{ ref('dim_venue') }}
where (indoor_basis = 'unknown' and has_indoor is not null)
   or (indoor_basis <> 'unknown' and has_indoor is null)
