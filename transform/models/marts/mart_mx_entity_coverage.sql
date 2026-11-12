-- Pin counts for each of Mexico's 32 federal entities (31 states + Mexico City; docs/mexico_states_outline.md, ADR 0034).
-- One row per entity, including entities with no pins yet. hand_built = pins from a seed row a person added (venue_source
-- 'manual', which includes the OSM or Overture records merged into one); automatic = pins from OSM or Overture alone (labelled inferred).
select
    e.subregion,
    e.entity_name,
    e.entity_type,
    count(v.venue_id)                                                   as pins,
    count(*) filter (where v.venue_source = 'manual')                   as hand_built,
    count(*) filter (where v.venue_id is not null and v.venue_source <> 'manual') as automatic,
    count(*) filter (where v.venue_kind = 'hitting_wall')               as wall_pins,
    count(*) filter (where v.is_confirmed_public)                       as confirmed_public
from {{ ref('mx_entities') }} e
left join {{ ref('dim_venue') }} v on v.subregion = e.subregion
group by 1, 2, 3
