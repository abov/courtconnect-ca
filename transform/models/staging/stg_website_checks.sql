-- Does each listed website still exist? Two sources, hand overrides first:
--   1. seeds/website_overrides.csv: sites a person found to be parked, hijacked or the wrong business. DNS cannot see these
--      (a parked domain still resolves), so a human flag wins over the automatic result.
--   2. ingestion/check_websites.py: DNS-only check. status ok | dead (domain does not exist) | unknown (inconclusive, never treated as dead).
with overrides as (
    select
        lower(trim(domain))                                   as domain,
        lower(trim(status))                                   as status,
        cast(null as varchar)                                 as resolved_host,
        cast(verified_on as varchar)                          as checked_at
    from {{ ref('website_overrides') }}
),

checks as (
    select
        domain,
        status,
        nullif(resolved_host, '')                             as resolved_host,
        cast(checked_at as varchar)                           as checked_at
    from {{ source('raw', 'website_checks') }}
    where domain is not null
)

select * from overrides
union all
select * from checks where domain not in (select domain from overrides)
