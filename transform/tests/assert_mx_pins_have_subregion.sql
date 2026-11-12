{{ config(severity='warn') }}
-- Every Mexican pin belongs to one of the 32 federal entities. Fails when a new or moved MX pin has no row in seeds/venue_subregion.csv:
-- run `python ingestion/subregion_from_boundaries.py` and rebuild.
select venue_id, venue_name, lat, lon
from {{ ref('dim_venue') }}
where region = 'MX' and subregion is null
