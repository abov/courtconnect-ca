-- Named areas (parks, schools, clubs...) with bounding boxes, used to name unnamed courts.
select
    osm_type || '/' || cast(osm_id as varchar)                as parent_id,
    trim(name)                                                as parent_name,
    kind                                                      as osm_kind,
    case
        when kind in ('leisure=park', 'leisure=garden', 'leisure=recreation_ground')                  then 'park'
        when kind in ('leisure=sports_centre', 'leisure=stadium', 'leisure=fitness_centre', 'club=sport') then 'sports_facility'
        when kind in ('amenity=school', 'amenity=college', 'amenity=university')                      then 'school'
        when kind in ('amenity=community_centre', 'amenity=clubhouse')                                then 'community'
        else 'resort_or_other'
    end                                                       as kind_group,
    cast(minlat as double)                                    as minlat,
    cast(minlon as double)                                    as minlon,
    cast(maxlat as double)                                    as maxlat,
    cast(maxlon as double)                                    as maxlon,
    (cast(maxlat as double) - cast(minlat as double))
      * (cast(maxlon as double) - cast(minlon as double))     as bbox_area_deg2
from {{ source('raw', 'osm_parents') }}
where name is not null and trim(name) <> ''
