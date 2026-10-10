-- One row per Overture place, linked to an OSM venue when one is within `place_match_radius_m` metres.
-- venue_id is the venue the place belongs to: the matched OSM venue, otherwise a venue of its own.
with strong as (
    select place_id, count(distinct sport_id) as strong_sport_count
    from {{ ref('bridge_place_sport') }}
    where evidence = 'strong'
    group by 1
)

select
    p.place_id,
    p.place_name,
    p.category,
    p.lat,
    p.lon,
    p.confidence,
    p.website,
    {{ website_domain('p.website') }}                         as website_domain,
    {{ website_status('p.website', 'w.status') }}             as website_status,
    p.phone,
    p.address_line,
    p.city,
    p.postcode,
    p.license,
    p.release,
    m.venue_id                                                as matched_venue_id,
    m.distance_m                                              as match_distance_m,
    coalesce(m.venue_id, md5('place/' || p.place_id))         as venue_id,
    coalesce(s.strong_sport_count, 0)                         as strong_sport_count,
    coalesce(s.strong_sport_count, 0) > 0                     as has_strong_sport
from {{ ref('stg_overture_places') }} p
left join {{ ref('int_place_venue_match') }} m on m.place_id = p.place_id
left join strong s on s.place_id = p.place_id
left join {{ ref('stg_website_checks') }} w on w.domain = {{ website_domain('p.website') }}
