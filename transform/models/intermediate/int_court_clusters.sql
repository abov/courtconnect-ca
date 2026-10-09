-- Groups courts into facilities: connected components of the "within N metres" graph.
-- Portable SQL (no recursion, no UDFs): every court starts with its own id as a label and,
-- on each pass, adopts the smallest label among its neighbours. Labels flood outward from
-- the smallest id in each group, so after enough passes everyone in a facility shares one label.
-- `changed_in_last_pass` lets a dbt test prove we ran enough passes (see assert_clusters_converged).
{% set passes = 8 %}

with pairs as (
    select * from {{ ref('int_court_pairs') }}
),

l0 as (
    select court_id, court_id as label from {{ ref('stg_osm_courts') }}
)
{% for i in range(1, passes + 1) %}
, l{{ i }} as (
    select
        c.court_id,
        least(c.label, coalesce(min(n.label), c.label)) as label
    from l{{ i - 1 }} c
    left join pairs p on p.court_a = c.court_id
    left join l{{ i - 1 }} n on n.court_id = p.court_b
    group by c.court_id, c.label
)
{% endfor %}

select
    a.court_id,
    a.label                       as cluster_label,
    (a.label <> b.label)          as changed_in_last_pass
from l{{ passes }} a
join l{{ passes - 1 }} b on b.court_id = a.court_id
