-- Regions in hide_unverified_regions (Mexico) list only hand-verified venues: a manual seed row must back every pin.
select venue_id, venue_name, region
from {{ ref('mart_venue_finder') }}
where region in ('{{ var("hide_unverified_regions") | join("', '") }}')
  and name_source <> 'manual'
  and not in_manual
