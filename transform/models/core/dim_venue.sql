-- One row per facility.
--   venue_source 'osm'         : courts grouped by proximity (ADR 0003), no matching place
--   venue_source 'osm+places'  : the same, plus an Overture place within `place_match_radius_m` that adds a name, website, phone, address
--   venue_source 'places_only' : a racket-sport place Overture knows about that OpenStreetMap has no court for (indoor clubs, gyms...)
-- Name precedence: tagged on the court > operator > Overture place name (confidence >= 0.5) > enclosing park/school/club
-- (approximate, ADR 0004) > unnamed.
with courts as (
    select * from {{ ref('dim_court') }}
),

sports as (
    select venue_id, count(distinct sport_id) as sport_count
    from {{ ref('bridge_venue_sport') }}
    group by 1
),

best_parent as (
    select venue_id, parent_name, parent_kind
    from (
        select venue_id, parent_name, parent_kind,
               row_number() over (partition by venue_id order by parent_area asc, parent_name) as rn
        from courts
        where parent_name is not null
    ) x
    where rn = 1
),

best_place as (
    select matched_venue_id as venue_id, place_name, website, phone, address_line, city, confidence
    from (
        select *, row_number() over (partition by matched_venue_id order by confidence desc, place_id) as rn
        from {{ ref('dim_place') }}
        where matched_venue_id is not null and has_strong_sport
    ) x
    where rn = 1
),

-- Hand-added venues that matched a venue we already hold (int_manual_venue_match): they enrich it, they do not duplicate it.
best_manual as (
    select
        mm.effective_venue_id                                 as venue_id,
        min(m.venue_name)                                     as venue_name,
        min(m.website)                                        as website,
        min(m.offerings)                                      as offerings,
        max(case when m.access_type = 'public' then 1 else 0 end) = 1 as is_public,
        max(case when m.access_type in ('private', 'members') then 1 else 0 end) = 1 as is_members
    from {{ ref('stg_manual_venues') }} m
    join {{ ref('int_manual_venue_match') }} mm on mm.venue_key = m.venue_key
    where mm.is_matched
    group by mm.effective_venue_id
),

osm_venues as (
    select
        venue_id,
        -- digit-only court names ("1", "2") are court numbers, not venue names
        min(case when translate(court_name, '0123456789 ', '') <> '' then court_name end) as tagged_name,
        min(operator_name)                                    as operator_name,
        sum(case when record_kind = 'court' then 1 else 0 end)    as court_records,
        sum(case when record_kind = 'facility' then 1 else 0 end) as facility_records,
        avg(lat)                                              as lat,
        avg(lon)                                              as lon,
        min(website)                                          as website,
        min(phone)                                            as phone,
        min(opening_hours)                                    as opening_hours,
        min(address_line)                                     as address_line,
        min(city)                                             as city,
        min(region)                                           as region,   -- one venue, one region (a cluster on the border takes the first code)
        max(case when is_lit then 1 else 0 end) = 1                   as has_lit_courts,
        max(case when access_type = 'public' then 1 else 0 end) = 1   as is_confirmed_public,
        max(case when access_type in ('private', 'members') then 1 else 0 end) = 1 as has_members_courts,
        max(case when is_free then 1 else 0 end) = 1                  as has_free_courts,
        -- indoor is three-valued: true (a court is tagged indoor), false (a court is tagged outdoor/covered, none indoor), null = unknown
        -- (untagged pitches are 'likely_outdoor', an assumption, so they do not count as evidence)
        case when max(case when setting = 'indoor' then 1 else 0 end) = 1 then true
             when max(case when setting in ('outdoor', 'covered') then 1 else 0 end) = 1 then false end as has_indoor,
        max(case when setting in ('outdoor', 'likely_outdoor', 'covered') then 1 else 0 end) = 1 as has_outdoor,
        max(case when surface_type = 'hard' then 1 else 0 end) = 1    as has_hard,
        max(case when surface_type = 'clay' then 1 else 0 end) = 1    as has_clay,
        max(case when surface_type = 'grass' then 1 else 0 end) = 1   as has_grass,
        max(case when surface_type = 'turf' then 1 else 0 end) = 1    as has_turf,
        max(case when surface_type = 'sand' then 1 else 0 end) = 1    as has_sand,
        max(case when surface_type in ('carpet', 'wood') then 1 else 0 end) = 1 as has_indoor_floor
    from courts
    group by venue_id
),

-- A hand-checked name for a court group a nearby club place names (seeds/venue_name_official.csv); counts only while the pin is where it was checked.
official_name as (
    select o.venue_id, o.venue_name
    from {{ ref('venue_name_official') }} o
    join osm_venues v on v.venue_id = o.venue_id
    where abs(v.lat - cast(o.lat as double)) < 0.0003 and abs(v.lon - cast(o.lon as double)) < 0.0003
),

osm_final as (
    select
        v.venue_id,
        coalesce(v.tagged_name, v.operator_name, bm.venue_name, on_.venue_name,
                 case when pl.confidence >= 0.5 then pl.place_name end, pp.parent_name)   as venue_name,
        case
            when v.tagged_name is not null                      then 'court_name'
            when v.operator_name is not null                    then 'operator'
            when bm.venue_name is not null                      then 'manual'
            when on_.venue_name is not null                     then 'manual'
            when pl.confidence >= 0.5                           then 'places_directory'
            when pp.parent_name is not null                     then 'enclosing_feature'
            else 'unnamed'
        end                                                   as name_source,
        case when v.tagged_name is null and v.operator_name is null and bm.venue_name is null and on_.venue_name is null
                  and coalesce(pl.confidence, 0) < 0.5 then pp.parent_kind end            as name_feature_kind,
        case when pl.venue_id is not null then 'osm+places' else 'osm' end                as venue_source,
        v.court_records,
        v.facility_records,
        v.lat, v.lon,
        coalesce(v.website, bm.website, pl.website)           as website,
        coalesce(v.phone, pl.phone)                           as phone,
        v.opening_hours,
        coalesce(v.address_line, pl.address_line)             as address_line,
        coalesce(v.city, pl.city)                             as city,
        v.region,
        bm.offerings                                          as offerings,
        v.has_lit_courts, (v.is_confirmed_public or coalesce(bm.is_public, false)) as is_confirmed_public, v.has_free_courts,
        -- members-only = marked private/members and nothing says public (the only access signal we hold; unmarked venues are NOT assumed public)
        ((v.has_members_courts or coalesce(bm.is_members, false)) and not (v.is_confirmed_public or coalesce(bm.is_public, false))) as is_members_only,
        v.has_indoor, v.has_outdoor,
        case when v.has_indoor is not null then 'osm_tag' else 'unknown' end              as indoor_basis,
        v.has_hard, v.has_clay, v.has_grass, v.has_turf, v.has_sand, v.has_indoor_floor,
        cast(null as varchar)                                 as also_listed_as
    from osm_venues v
    left join best_parent pp on pp.venue_id = v.venue_id
    left join best_place pl on pl.venue_id = v.venue_id
    left join best_manual bm on bm.venue_id = v.venue_id
    left join official_name on_ on on_.venue_id = v.venue_id
),

-- Places that share an address are one venue (dim_place.venue_id): the best-confidence record names it, the others are
-- kept as `also_listed_as`, and a website/phone missing on the best record is taken from the others.
places_ranked as (
    select
        p.*,
        row_number() over (
            partition by p.venue_id
            order by p.confidence desc, case when p.website is not null then 0 else 1 end, p.place_id
        ) as rn
    from {{ ref('dim_place') }} p
    where p.matched_venue_id is null and p.has_strong_sport
),

place_group_extra as (
    select
        venue_id,
        min(website)                                                          as any_website,
        min(phone)                                                            as any_phone,
        min(address_line)                                                     as any_address,
        listagg(distinct case when rn > 1 then place_name end, ' | ') as also_listed_as
    from places_ranked
    group by 1
),

places_only as (
    select
        p.venue_id,
        p.place_name                                          as venue_name,
        'places_directory'                                    as name_source,
        cast(null as varchar)                                 as name_feature_kind,
        'places_only'                                         as venue_source,
        0                                                     as court_records,
        1                                                     as facility_records,
        p.lat, p.lon,
        coalesce(p.website, x.any_website, bm.website)        as website,
        coalesce(p.phone, x.any_phone)                        as phone,
        cast(null as varchar)                                 as opening_hours,
        coalesce(p.address_line, x.any_address)               as address_line,
        p.city,
        p.region,
        bm.offerings                                          as offerings,
        false as has_lit_courts, coalesce(bm.is_public, false) as is_confirmed_public, false as has_free_courts,
        (coalesce(bm.is_members, false) and not coalesce(bm.is_public, false)) as is_members_only,
        cast(null as boolean) as has_indoor, false as has_outdoor,   -- an Overture place says nothing about indoor/outdoor: unknown, not "outdoor"
        'unknown'                                             as indoor_basis,
        false as has_hard, false as has_clay, false as has_grass, false as has_turf, false as has_sand, false as has_indoor_floor,
        x.also_listed_as
    from places_ranked p
    join place_group_extra x on x.venue_id = p.venue_id
    left join best_manual bm on bm.venue_id = p.venue_id
    where p.rn = 1
),

-- Hand-curated venues (seeds/manual_venues.csv): one row per venue, with what it offers.
manual_final as (
    select
        venue_id,
        min(venue_name)                                       as venue_name,
        'manual'                                              as name_source,
        cast(null as varchar)                                 as name_feature_kind,
        'manual'                                              as venue_source,
        coalesce(max(courts_count), 0)                        as court_records,
        1                                                     as facility_records,
        min(lat)                                              as lat,
        min(lon)                                              as lon,
        min(website)                                          as website,
        cast(null as varchar)                                 as phone,
        cast(null as varchar)                                 as opening_hours,
        cast(null as varchar)                                 as address_line,
        min(city)                                             as city,
        min(region)                                           as region,
        min(offerings)                                        as offerings,
        false as has_lit_courts,
        max(case when access_type = 'public' then 1 else 0 end) = 1 as is_confirmed_public,
        false as has_free_courts,
        max(case when access_type in ('private', 'members') then 1 else 0 end) = 1
            and max(case when access_type = 'public' then 1 else 0 end) = 0 as is_members_only,
        case when max(case when setting = 'indoor' then 1 else 0 end) = 1 then true
             when max(case when setting in ('outdoor', 'covered') then 1 else 0 end) = 1 then false end as has_indoor,   -- blank / unknown / likely_outdoor = unknown
        max(case when setting in ('outdoor', 'likely_outdoor', 'covered') then 1 else 0 end) = 1 as has_outdoor,
        case when max(case when setting in ('indoor', 'outdoor', 'covered') then 1 else 0 end) = 1 then 'manual_seed' else 'unknown' end as indoor_basis,
        max(case when surface_type = 'hard' then 1 else 0 end) = 1    as has_hard,
        max(case when surface_type = 'clay' then 1 else 0 end) = 1    as has_clay,
        max(case when surface_type = 'grass' then 1 else 0 end) = 1   as has_grass,
        max(case when surface_type = 'turf' then 1 else 0 end) = 1    as has_turf,
        max(case when surface_type = 'sand' then 1 else 0 end) = 1    as has_sand,
        false as has_indoor_floor,
        cast(null as varchar)                                 as also_listed_as
    from {{ ref('stg_manual_venues') }} m
    join {{ ref('int_manual_venue_match') }} mm on mm.venue_key = m.venue_key
    where not mm.is_matched
    group by m.venue_id
),

unioned as (
    select * from osm_final
    union all
    select * from places_only
    union all
    select * from manual_final
)

select
    u.*,
    {{ website_status('u.website', 'wc.status') }}            as website_status,   -- ok | dead | unknown | unchecked; null = no website
    g.google_place_id,                                         -- ID only; the app fetches details live (ADR 0005)
    coalesce(s.sport_count, 0)                                as sport_count
from unioned u
left join sports s on s.venue_id = u.venue_id
left join {{ ref('stg_google_place_ids') }} g on g.venue_id = u.venue_id
left join {{ ref('stg_website_checks') }} wc on wc.domain = {{ website_domain('u.website') }}
