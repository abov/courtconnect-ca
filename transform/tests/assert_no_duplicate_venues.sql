-- Guard against the same facility being listed twice (e.g. one school's courts as three pins, or two Overture listings of
-- one address). Two venues with the same name within 150 m fail the build; fix by merging (int_court_pairs / dim_place)
-- or, for hand-added venues, by an entry in manual_venue_matches / a name fix. Hand-added pairs are left to review.
{% set d %}sqrt(power((a.lat - b.lat) * 110540, 2) + power((a.lon - b.lon) * cos(radians(a.lat)) * 111320, 2)){% endset %}
select a.venue_id as venue_a, b.venue_id as venue_b, a.venue_name, round({{ d }}) as distance_m
from {{ ref('dim_venue') }} a
join {{ ref('dim_venue') }} b
  on a.venue_id < b.venue_id
 and lower(a.venue_name) = lower(b.venue_name)
 and abs(a.lat - b.lat) < 0.002 and abs(a.lon - b.lon) < 0.003
where {{ d }} <= 150
  and not (a.venue_source = 'manual' and b.venue_source = 'manual')
  and a.name_source <> 'unnamed' and b.name_source <> 'unnamed'
