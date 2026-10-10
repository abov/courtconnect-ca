-- How trustworthy are the websites we hold? One row per source and confidence band.
-- Answers: does Overture's confidence score predict a dead website? (It does not.)
-- 'dead' = the domain no longer exists (DNS). 'unknown' checks are excluded from the dead rate.
with all_sites as (
    select
        'overture'                                            as source,
        case
            when confidence >= 0.9 then 'confidence 0.9-1.0'
            when confidence >= 0.5 then 'confidence 0.5-0.9'
            else 'confidence below 0.5'
        end                                                   as band,
        website_status
    from {{ ref('dim_place') }}
    where website is not null

    union all

    select 'osm', 'all', {{ website_status('c.website', 'w.status') }}
    from {{ ref('dim_court') }} c
    left join {{ ref('stg_website_checks') }} w on w.domain = {{ website_domain('c.website') }}
    where c.website is not null

    union all

    select 'manual', 'all', {{ website_status('m.website', 'w.status') }}
    from {{ ref('stg_manual_venues') }} m
    left join {{ ref('stg_website_checks') }} w on w.domain = {{ website_domain('m.website') }}
    where m.website is not null
)

select
    source,
    band,
    count(*)                                                  as listings_with_website,
    sum(case when website_status in ('ok', 'dead') then 1 else 0 end)  as checked,
    sum(case when website_status = 'dead' then 1 else 0 end)           as dead,
    sum(case when website_status = 'unknown' then 1 else 0 end)        as inconclusive,
    sum(case when website_status = 'unchecked' then 1 else 0 end)      as not_yet_checked,
    case when sum(case when website_status in ('ok', 'dead') then 1 else 0 end) = 0 then null
         else round(100.0 * sum(case when website_status = 'dead' then 1 else 0 end)
                    / sum(case when website_status in ('ok', 'dead') then 1 else 0 end), 1) end as pct_dead
from all_sites
group by 1, 2
