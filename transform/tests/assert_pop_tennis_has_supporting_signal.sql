-- Pop Tennis / paddle tennis (open court, low net) gets mixed up with Padel (walled glass court) in OSM tags and names (padel audit, 2026-10-17).
-- Padel has its own stricter test (assert_padel_has_supporting_signal). A Pop Tennis row needs a direct signal that is not a derivation:
--   allowed: confirmed or reported by a person (rungs 1-2), an Overture category (5), or a business-name word (6, stays in the review queue);
--   a loose OSM tag (4) only while it is flagged needs_review. A high-confidence OSM tag (3) or a derived row (7) is never enough.
-- To clear a failure: confirm the place in manual_venues / place_sport_overrides, reject a wrong OSM tag in osm_court_sport_overrides
-- (or re-identify it with correct_sport), or lower the tag's confidence in osm_sport_map.
select v.venue_name, e.sport_name, e.best_rung_label
from {{ ref('mart_sport_evidence') }} e
join {{ ref('dim_venue') }} v on v.venue_id = e.venue_id
where e.sport_name = 'Pop Tennis'
  and (e.best_rung in (3, 7) or (e.best_rung >= 4 and not e.needs_review))
