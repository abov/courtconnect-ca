-- A community report on an existing map venue (ci/issue_to_pr.py) is written at that pin's coordinates and must merge onto it,
-- not onto a neighbouring venue and not as a pin of its own. Warn only: map ids change when venues re-cluster, so a hit means
-- "a reviewer should look", not "the data is wrong".
{{ config(severity='warn') }}
select m.venue_key, m.location_precision, mm.effective_venue_id
from {{ ref('stg_manual_venues') }} m
join {{ ref('int_manual_venue_match') }} mm on mm.venue_key = m.venue_key
where m.location_precision like 'pin: map id %'
  and (not mm.is_matched
       or substr(mm.effective_venue_id, 1, 10) <> substr(m.location_precision, 13, 10))
