-- Every racket sport on the master sheet, with an honest status and what to do about it.
--   covered            : 5+ venues found
--   sparse             : 1-4 venues found
--   tagged_none_found  : OpenStreetMap has a tag for it but nothing is mapped in California
--   no_osm_tag         : OpenStreetMap has no tag for this sport at all -> needs another source
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
    coalesce(cov.courts_found, 0)                             as courts_found,
    case
        when coalesce(t.osm_tag_count, 0) = 0                 then 'no_osm_tag'
        when coalesce(cov.venues_found, 0) = 0                then 'tagged_none_found'
        when cov.venues_found < 5                             then 'sparse'
        else 'covered'
    end                                                       as coverage_status,
    case
        when coalesce(t.osm_tag_count, 0) = 0
            then 'Places API keyword search + governing-body / club directory'
        when coalesce(cov.venues_found, 0) = 0
            then 'Add to OSM or Places API; verify the tag mapping'
        when cov.venues_found < 5
            then 'Supplement with Places API and club directories'
        else 'OpenStreetMap is sufficient; enrich names and hours'
    end                                                       as recommended_next_source
from {{ ref('dim_sport') }} s
left join tags t on t.sport = s.sport_name
left join cov on cov.sport_name = s.sport_name
where s.sport_family like 'Racket%'
