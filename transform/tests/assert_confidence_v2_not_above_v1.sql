-- The sport penalty can only lower a score, and only by up to 15 points.
select venue_id, confidence_score_v1, confidence_score
from {{ ref('mart_venue_confidence') }}
where confidence_score > confidence_score_v1 or confidence_score_v1 - confidence_score > 15
