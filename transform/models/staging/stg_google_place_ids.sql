-- Google place IDs for our venues. Place IDs are the only Google Places content Google lets you store
-- (ingestion/google_place_ids.py stores nothing else). Empty until someone runs that script with an API key.
select
    venue_id,
    google_place_id,
    resolved_at
from {{ source('raw', 'google_place_ids') }}
where venue_id is not null and google_place_id is not null
