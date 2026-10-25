-- Google Trends "interest by metro" on ONE scale (docs/search_interest_plan.md). Relative, sampled searches; not volumes, not people.
-- Each Trends query scales a sport to 100 at its top metro, and the California and Nevada queries have different tops. Reno is in both,
-- so Las Vegas (Nevada query only) is rescaled onto the California scale by Reno's ratio. No Reno data in either query = no Las Vegas index.
--   index_source : california_query | nevada_query_rescaled_via_reno | no_data
--   confidence   : ok (the five busiest sports) | thin (low-volume terms: Trends samples them, so values are noisy)
with raw as (
    select
        query_geo,
        metro_code,
        sport,
        term,
        query_set,
        exported_on,
        try_cast(index_value as double)  as index_value
    from {{ ref('search_interest') }}
),

ca as (
    select * from raw where query_geo = 'US-CA'
),

nv as (
    select * from raw where query_geo = 'US-NV'
),

reno_bridge as (
    select ca.sport, ca.index_value / nv.index_value as factor
    from ca
    join nv on nv.sport = ca.sport and nv.metro_code = ca.metro_code
    where ca.metro_code = 811 and ca.index_value > 0 and nv.index_value > 0
),

unioned as (
    select sport, term, metro_code, query_set, exported_on, index_value,
           case when index_value is null then 'no_data' else 'california_query' end as index_source
    from ca
    union all
    select nv.sport, nv.term, nv.metro_code, nv.query_set, nv.exported_on,
           round(nv.index_value * b.factor, 0)                                        as index_value,
           case when nv.index_value is null or b.factor is null then 'no_data' else 'nevada_query_rescaled_via_reno' end as index_source
    from nv
    left join reno_bridge b on b.sport = nv.sport
    where nv.metro_code <> 811
)

select
    u.metro_code,
    m.metro_name,
    u.sport,
    u.term,
    u.index_value,
    u.index_source,
    case when u.query_set = 'A' then 'ok' else 'thin' end as confidence,
    u.exported_on
from unioned u
join {{ ref('search_metros') }} m on m.metro_code = u.metro_code
