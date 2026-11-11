-- Named areas (parks, schools, clubs...) with bounding boxes, used to name unnamed courts.
-- Multi-campus guard: a school/college/university whose box is over 0.005 deg2 (about 5 x 10 km) is a relation that
-- joins separate campuses, not one site, so its box says nothing about where its courts are. The only one in the data
-- is Hawaii Pacific University (relation 15638112, Waikiki to Kaneohe to Waimanalo: it named a dozen public Honolulu
-- courts; next largest school is UC Davis at 0.0025). Single-campus members like way/440675973 stay.
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
      * (cast(maxlon as double) - cast(minlon as double))     as bbox_area_deg2,
    -- the address mapped on the feature itself (addr:housenumber + addr:street), when someone tagged one
    case when nullif(trim(addr_housenumber), '') is not null and nullif(trim(addr_street), '') is not null
         then case when region = 'MX' then trim(addr_street) || ' ' || trim(addr_housenumber)   -- Mexico writes street then number (ADR 0034)
                   else trim(addr_housenumber) || ' ' || trim(addr_street) end end   as address_line,
    nullif(trim(addr_city), '')                               as addr_city
from {{ source('raw', 'osm_parents') }}
where name is not null and trim(name) <> ''
  and not (
      kind in ('amenity=school', 'amenity=college', 'amenity=university')
      and (cast(maxlat as double) - cast(minlat as double)) * (cast(maxlon as double) - cast(minlon as double)) > 0.005
  )
