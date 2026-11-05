-- Venues the build holds but the map does not show: automatic OSM + Overture venues in a verified-only region (var verified_only_regions, ADR 0034)
-- that have no seed row with evidence (int_venue_verified). They are LEADS, not facts: the trial (docs/mexico_metro_trial.md) found about 1 in 5
-- of the named ones real and current. To pin one, verify it from a public page and add a manual_venues row (or a venue_actions row).
select
    v.venue_id,
    coalesce(dn.display_name, v.venue_name, 'Unnamed courts') as venue_name,
    v.name_source,
    v.venue_source,
    v.region,
    a.city,
    v.lat,
    v.lon,
    v.website,
    v.phone,
    string_agg(distinct s.sport_name, '; ' order by s.sport_name) as sports
from {{ ref('dim_venue') }} v
join {{ ref('int_venue_address') }} a on a.venue_id = v.venue_id
left join {{ ref('int_venue_display_name') }} dn on dn.venue_id = v.venue_id
join {{ ref('bridge_venue_sport') }} b on b.venue_id = v.venue_id
join {{ ref('dim_sport') }} s on s.sport_id = b.sport_id
where v.region in ({% for r in var('verified_only_regions') %}'{{ r }}'{% if not loop.last %}, {% endif %}{% endfor %})
  and v.venue_id not in (select venue_id from {{ ref('int_venue_verified') }})
group by v.venue_id, dn.display_name, v.venue_name, v.name_source, v.venue_source, v.region, a.city, v.lat, v.lon, v.website, v.phone
