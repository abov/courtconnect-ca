-- Every racket sport on the master sheet, with an honest status and what to do about it.
--   covered            : 5+ venues found
--   sparse             : 1-4 venues found
--   possible_only      : no confirmed venue, but some business names mention it (weak matches, review them)
--   tagged_none_found  : OpenStreetMap has a tag for it, but nothing is mapped in California
--   not_found          : no OpenStreetMap tag and no place found: needs a club / governing-body directory
with tags as (
    select sport, count(*) as osm_tag_count, min(confidence) as worst_confidence
    from {{ ref('osm_sport_map') }}
    group by sport
),

cov as (
    select * from {{ ref('mart_sport_coverage') }}
)

select
    s.sport_name,
    s.popularity_class,
    s.governing_body,
    s.official_url,
    coalesce(t.osm_tag_count, 0) > 0                          as has_osm_tag,
    t.worst_confidence                                        as osm_mapping_confidence,
    coalesce(cov.venues_found, 0)                             as venues_found,
    coalesce(cov.osm_venues, 0)                               as osm_venues,
    coalesce(cov.places_venues, 0)                            as places_venues,
    coalesce(cov.courts_found, 0)                             as courts_found,
    coalesce(cov.weak_name_matches, 0)                        as weak_name_matches,
    case
        when coalesce(cov.venues_found, 0) >= 5               then 'covered'
        when coalesce(cov.venues_found, 0) >= 1               then 'sparse'
        when coalesce(cov.weak_name_matches, 0) > 0           then 'possible_only'
        when coalesce(t.osm_tag_count, 0) > 0                 then 'tagged_none_found'
        else 'not_found'
    end                                                       as coverage_status,
    case
        when coalesce(cov.venues_found, 0) >= 5               then 'OpenStreetMap and the places directory are sufficient; enrich names and hours'
        when coalesce(cov.venues_found, 0) >= 1               then 'Supplement with club directories and the governing-body list'
        when coalesce(cov.weak_name_matches, 0) > 0           then 'Review the weak name matches in mart_places_to_review'
        when coalesce(t.osm_tag_count, 0) > 0                 then 'Nothing mapped in California yet: check governing-body and club directories'
        else 'Governing-body or club directory, Meetup groups; Google place IDs for live lookup'
    end                                                       as recommended_next_source
from {{ ref('dim_sport') }} s
left join tags t on t.sport = s.sport_name
left join cov on cov.sport_name = s.sport_name
where s.sport_family like 'Racket%'
