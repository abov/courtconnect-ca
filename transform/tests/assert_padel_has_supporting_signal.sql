-- Guard rail from the 2026-10-17 padel audit: most OpenStreetMap `sport=padel` tags (aerial-imagery passes) and name-only matches were wrong
-- (pickleball, backyard courts, pop tennis). A Padel venue must rest on a person's evidence: a hand-added venue with a club or official page
-- (rung 1 confirmed) or an owner / community report (rung 2 reported). An OSM tag alone (rung 3-4), an Overture category (5) or a business-name
-- word (6) is not enough: confirm the club on its own page (manual_venues.csv or a place_sport_overrides confirm), correct the court with
-- osm_court_sport_overrides.csv, or reject it. Rows returned here are Padel venues with no such evidence.
select
    v.venue_name,
    v.city,
    e.best_rung_label
from {{ ref('mart_sport_evidence') }} e
join {{ ref('dim_venue') }} v on v.venue_id = e.venue_id
where e.sport_name = 'Padel'
  and e.best_rung > 2
