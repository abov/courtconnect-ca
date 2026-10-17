-- Groups OpenStreetMap walls that stand side by side (a school's row of handball courts) into one map pin: connected
-- components of the "same wall type, within `wall_group_radius_m`" graph, labelled the same way as int_court_clusters
-- (each wall adopts the smallest key among its neighbours on every pass). Hand-added walls are never grouped: each one
-- was reported on its own. The wall set is small (under a thousand), so a plain self-join is enough here.
-- `changed_in_last_pass` lets assert_wall_clusters_converged prove we ran enough passes.
{% set passes = 8 %}

with walls as (
    select wall_key, wall_type, lat, lon from {{ ref('dim_wall') }}
),

pairs as (
    select a.wall_key as wall_a, b.wall_key as wall_b
    from walls a
    join walls b
        on b.wall_key <> a.wall_key
       and b.wall_type = a.wall_type
       and abs(b.lat - a.lat) < 0.01
    where a.wall_key like 'osm-%' and b.wall_key like 'osm-%'
      and sqrt(
              power((a.lat - b.lat) * 110540, 2)
            + power((a.lon - b.lon) * cos(radians(a.lat)) * 111320, 2)
          ) <= {{ var('wall_group_radius_m') }}
),

l0 as (
    select wall_key, wall_key as label from walls
)
{% for i in range(1, passes + 1) %}
, l{{ i }} as (
    select
        c.wall_key,
        least(c.label, coalesce(min(n.label), c.label)) as label
    from l{{ i - 1 }} c
    left join pairs p on p.wall_a = c.wall_key
    left join l{{ i - 1 }} n on n.wall_key = p.wall_b
    group by c.wall_key, c.label
)
{% endfor %}

select
    a.wall_key,
    a.label                       as wall_group,
    (a.label <> b.label)          as changed_in_last_pass
from l{{ passes }} a
join l{{ passes - 1 }} b on b.wall_key = a.wall_key
