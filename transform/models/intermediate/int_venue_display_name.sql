-- Display name for every venue. Pins whose name is only INFERRED from an enclosing campus, club or park (name_source 'enclosing_feature')
-- often share one name inside a city (six "UC San Diego" pins in La Jolla). When 2+ venues share lower(name) + city, each inferred one gets
-- a computed suffix: "<direction from the group's centroid> courts, <N courts>", e.g. "UC San Diego (north courts, 6 courts)".
--   direction : 8-point compass of the venue relative to the centroid of ALL same-name venues in that city; "central" within 100 m of it
--   count     : dim_venue.court_records (mapped courts, all sports), else "court count unknown"
--   still equal after that (same direction and count): ", #1", ", #2"... by distance from the centroid, then venue_id
-- The suffix comes from position and court count, NOT from a source, so the name stays inferred (name_source / name quality unchanged).
-- Named by a person or a source (court_name, operator, manual, places_directory) are left alone: chain branches such as LA Fitness are
-- real separate places. venue_id is untouched. City is the final city (int_venue_address), so this cannot live in dim_venue.
with v as (
    select d.venue_id, d.venue_name, d.name_source, d.lat, d.lon, d.court_records, lower(a.city) as city_key
    from {{ ref('dim_venue') }} d
    join {{ ref('int_venue_address') }} a on a.venue_id = d.venue_id
    where d.name_source <> 'unnamed' and d.venue_name is not null and a.city is not null and d.lat is not null and d.lon is not null
),

grp as (
    select *,
           count(*) over (partition by lower(venue_name), city_key) as group_size,
           avg(lat) over (partition by lower(venue_name), city_key) as clat,
           avg(lon) over (partition by lower(venue_name), city_key) as clon
    from v
),

pos as (
    select *,
           (lon - clon) * cos(radians(clat)) * 111320            as dx,
           (lat - clat) * 110540                                 as dy
    from grp
    where group_size > 1 and name_source = 'enclosing_feature'
),

dir as (
    select *,
           sqrt(dx * dx + dy * dy)                               as dist_m,
           case
               when sqrt(dx * dx + dy * dy) < 100 then 'central'
               else (['north', 'northeast', 'east', 'southeast', 'south', 'southwest', 'west', 'northwest'])[
                        1 + cast(floor(((degrees(atan2(dx, dy)) + 360 + 22.5) % 360) / 45) as integer) % 8]
           end                                                   as direction,
           case when court_records > 0
                then cast(court_records as varchar) || case when court_records = 1 then ' court' else ' courts' end
                else 'court count unknown' end                   as count_label
    from pos
),

ranked as (
    select *,
           count(*) over (partition by lower(venue_name), city_key, direction, count_label) as same_label,
           row_number() over (partition by lower(venue_name), city_key, direction, count_label order by dist_m, venue_id) as ord
    from dir
)

select
    venue_id,
    venue_name || ' (' || direction || ' courts, ' || count_label
                || case when same_label > 1 then ', #' || cast(ord as varchar) else '' end || ')'   as display_name
from ranked
