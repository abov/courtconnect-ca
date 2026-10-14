-- The score must stay within 0-100.
select venue_id, confidence_score from {{ ref('mart_venue_confidence') }}
where confidence_score < 0 or confidence_score > 100
