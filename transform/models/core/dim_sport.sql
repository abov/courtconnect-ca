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
