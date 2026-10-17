-- Padel (walled glass court) and Pop Tennis / paddle tennis (open court, low net) get mixed up in OSM and in names (padel audit, 2026-10-17).
-- A row for either sport needs a direct signal that is not an unreviewed OSM tag or a derivation:
--   allowed: confirmed or reported by a person (rungs 1-2), an Overture category (5), or a business-name word (6, which stays in the review queue);
--   a loose OSM tag (4) is allowed only while it is flagged needs_review. A high-confidence OSM tag (3) or a derived row (7) is never enough:
--   the `padel` and pop tennis keys sit at medium confidence in osm_sport_map for exactly this reason.
-- To clear a failure: confirm the place in manual_venues / place_sport_overrides, reject a wrong OSM tag in osm_court_sport_overrides
-- (or re-identify it with correct_sport), or lower the tag's confidence in osm_sport_map.
select v.venue_name, e.sport_name, e.best_rung_label
from {{ ref('mart_sport_evidence') }} e
join {{ ref('dim_venue') }} v on v.venue_id = e.venue_id
where e.sport_name in ('Padel', 'Pop Tennis')
  and (e.best_rung in (3, 7) or (e.best_rung >= 4 and not e.needs_review))
