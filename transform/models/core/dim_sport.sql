select
    sport_id,
    sport_name,
    sport_family,
    popularity_class,
    governing_body,
    players_min,
    players_max,
    court_length_ft,
    court_width_ft,
    net_type,
    net_height_in,
    net_height_alt_in,
    surface_lc like '%concrete%'                              as plays_on_concrete,
    surface_lc like '%sand%'                                  as plays_on_sand,
    surface_lc like '%grass%'                                 as plays_on_grass,
    surface_lc like '%indoor%'                                as plays_indoors,
    -- the one surface a sport needs when the sheet lists no concrete, grass or sand for it (Padel = turf, Teq = curved table); null = no special surface.
    -- "Indoor/Outdoor" is not indoor-only. The "Find by court" dialog only offers such a sport courts of the same kind.
    case
        when surface_lc like '%concrete%' or surface_lc like '%grass%' or surface_lc like '%sand%' then null
        when surface_lc like '%curved table%' then 'curved_table'
        when surface_lc like '%tabletop%'     then 'tabletop'
        when surface_lc like '%turf%'         then 'turf'
        when surface_lc like '%aluminum%'     then 'aluminum'
        when surface_lc like '%indoor%' and surface_lc not like '%outdoor%' then 'indoor'
    end                                                       as special_surface,
    base_gear,
    gear_on_amazon_or_online,
    competitive_status,
    -- INFERRED tier from the sheet only (no venue or event data): 'established' = a world-federation sport (class World Official, competing),
    -- 'organized' = competing with a named governing body that is not flagged defunct/unsure, 'casual' = everything else.
    case
        when competitive_status = 'Competitive' and popularity_class = 'World Official' then 'established'
        when competitive_status = 'Competitive' and governing_body is not null
             and governing_body not like '%?%' and lower(governing_body) not like '%defunct%' then 'organized'
        else 'casual'
    end                                                       as competitive_tier,
    year_origin,
    official_url
from {{ ref('stg_sports') }}
