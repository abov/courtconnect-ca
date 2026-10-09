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
    surface_lc like '%concrete%'                              as plays_on_concrete,
    surface_lc like '%sand%'                                  as plays_on_sand,
    surface_lc like '%grass%'                                 as plays_on_grass,
    surface_lc like '%indoor%'                                as plays_indoors,
    base_gear,
    gear_on_amazon_or_online,
    competitive_status,
    year_origin,
    -- crude California-relevance flag from free-text location; refined later with real venue counts
    (loc_lc like '%ca%' or loc_lc like '%worldwide%' or loc_lc = 'us')  as likely_in_california,
    official_url
from {{ ref('stg_sports') }}
