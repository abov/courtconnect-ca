-- Physical sport-fit reference: which sports' playing areas fit inside another sport's court footprint.
-- Derived only from the sheet's court dimensions (dim_sport), so it is INFERRED, never "confirmed":
-- "fits" means the guest court's rectangle fits inside the host's (rotation allowed) and they share a surface type.
-- It does not say a venue allows the sport or has lines/nets for it. Not wired into the map yet.
with s as (
    select
        sport_name,
        greatest(court_length_ft, court_width_ft) as long_ft,
        least(court_length_ft, court_width_ft)    as short_ft,
        plays_on_concrete, plays_on_grass, plays_on_sand
    from {{ ref('dim_sport') }}
    where court_length_ft is not null and court_width_ft is not null
)

select
    h.sport_name                                         as host_sport,
    g.sport_name                                         as guest_sport,
    g.long_ft * g.short_ft                               as guest_area_sqft,
    h.long_ft * h.short_ft                               as host_area_sqft,
    round((g.long_ft * g.short_ft) / (h.long_ft * h.short_ft), 3) as area_ratio,
    -- 2+ guest courts side by side (same orientation) fit inside the host
    (floor(h.long_ft / g.long_ft) * floor(h.short_ft / g.short_ft)) as guest_courts_that_fit,
    'inferred'                                           as confirmation
from s h
join s g
  on g.sport_name <> h.sport_name
 and g.long_ft  <= h.long_ft
 and g.short_ft <= h.short_ft
 and (   (h.plays_on_concrete and g.plays_on_concrete)
      or (h.plays_on_grass    and g.plays_on_grass)
      or (h.plays_on_sand     and g.plays_on_sand))
