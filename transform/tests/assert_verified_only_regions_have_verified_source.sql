-- ADR 0034: a pin in a verified-only region (var verified_only_regions, today MX) reaches the map only with a hand-verified source:
-- a manual_venues row confirmed visited / official, or a venue_actions row with evidence + verified_on. Written from the staging tables,
-- not from int_venue_verified, so it checks the gate rather than repeating it.
select distinct f.venue_id, f.venue_name, f.region
from {{ ref('mart_venue_finder') }} f
where f.region in ({% for r in var('verified_only_regions') %}'{{ r }}'{% if not loop.last %}, {% endif %}{% endfor %})
  and f.venue_id not in (
        select mm.effective_venue_id
        from {{ ref('stg_manual_venues') }} m
        join {{ ref('int_manual_venue_match') }} mm on mm.venue_key = m.venue_key
        where m.confirmation_level in ('visited', 'official'))
  and f.venue_id not in (
        select venue_id from {{ ref('stg_venue_actions') }}
        where evidence is not null and verified_on is not null and venue_id is not null)
