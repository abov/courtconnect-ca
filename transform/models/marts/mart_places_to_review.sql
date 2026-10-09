-- Weak evidence: a business name contains an ambiguous sport word ("Camino Real Tennis Center" looks like Real Tennis but is
-- not). Never counted as a venue until you confirm them: add a row  place_id,sport,confirm  (or  reject)  to
-- transform/seeds/place_sport_overrides.csv and rebuild.
select
    bp.place_id,
    s.sport_name,
    bp.matched_term,
    p.place_name,
    p.category,
    p.city,
    p.website,
    p.confidence,
    p.lat,
    p.lon
from {{ ref('bridge_place_sport') }} bp
join {{ ref('dim_place') }} p on p.place_id = bp.place_id
join {{ ref('dim_sport') }} s on s.sport_id = bp.sport_id
where bp.evidence = 'weak'
