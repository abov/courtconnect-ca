-- Cleans the hand-maintained sports spreadsheet: fixes typos, parses messy
-- text (ranges, mixed units) into typed columns, and removes duplicates.
with src as (
    select * from {{ ref('all_racquet') }}
),

cleaned as (
    select
        md5(lower(trim(sport)))                               as sport_id,
        trim(sport)                                           as sport_name,
        trim(sport_type)                                      as sport_family,
        trim(popularity_class)                                as popularity_class,
        nullif(trim(org), '')                                 as governing_body,
        trim(active_loc)                                      as active_loc_raw,

        -- players: '2-4' -> 2/4, '2+' -> 2/null(open ended), '18' -> 18/18
        try_cast({{ regex_extract('players', '^([0-9]+)') }} as integer) as players_min,
        case
            when players like '%+' then null
            else try_cast(coalesce({{ regex_extract('players', '-([0-9]+)$') }}, {{ regex_extract('players', '^([0-9]+)$') }}) as integer)
        end                                                   as players_max,

        -- court: '44x20' -> 44 x 20 ft. Anything else (blocks, circumference, 'user descretion') stays null.
        try_cast({{ regex_extract('court_dim', '^([0-9.]+)x[0-9.]+$') }} as double) as court_length_ft,
        try_cast({{ regex_extract('court_dim', '^[0-9.]+x([0-9.]+)$') }} as double) as court_width_ft,

        lower(coalesce(court_surface, ''))                    as surface_lc,
        nullif(trim(base_gear), '')                           as base_gear,
        nullif(trim(net_type), '')                            as net_type,
        {{ to_inches('net_ht') }}                             as net_height_in,
        upper(trim(gear_avail_ao)) = 'Y'                      as gear_on_amazon_or_online,

        -- typo-proof: 'Competitve' / 'Non-Competitve' / blank
        case
            when lower(coalesce(competing, '')) like 'non%'   then 'Non-Competitive'
            when lower(coalesce(competing, '')) like 'comp%'  then 'Competitive'
            else 'Unknown'
        end                                                   as competitive_status,

        try_cast({{ regex_extract('year_origin', '^([0-9]{4})') }} as integer) as year_origin,
        nullif(trim(url), '')                                 as official_url,
        lower(coalesce(active_loc, ''))                       as loc_lc
    from src
    where sport is not null
),

deduped as (
    select *, row_number() over (partition by sport_id order by sport_name) as rn
    from cleaned
)

select * exclude (rn) from deduped where rn = 1
