-- Venues a person verified, from a seed row that carries evidence: the set that may reach the map in a verified-only region (var verified_only_regions, ADR 0034).
--   manual_venues      : a hand-added venue (or an automatic venue it merged into) confirmed 'visited' or 'official'; 'reported' is word of mouth, not verified
--   venue_actions      : a link-out row with `evidence` + `verified_on` pointing at the venue (a club page, a dated event)
-- The export shows the first kind with cf = 'v' / 'o'. Automatic OSM + Overture venues are in neither set until someone adds a seed row.
select mm.effective_venue_id as venue_id, 'manual_venues' as verified_via
from {{ ref('stg_manual_venues') }} m
join {{ ref('int_manual_venue_match') }} mm on mm.venue_key = m.venue_key
where m.confirmation_level in ('visited', 'official')
group by 1

union all

select venue_id, 'venue_actions'
from {{ ref('stg_venue_actions') }}
where evidence is not null and verified_on is not null and venue_id is not null
group by 1
