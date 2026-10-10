-- Result of ingestion/check_websites.py: does each website's domain still exist? (DNS only.)
-- status: ok | dead (definitively does not exist) | unknown (check inconclusive; never treated as dead)
select
    domain,
    status,
    nullif(resolved_host, '')                                 as resolved_host,
    checked_at
from {{ source('raw', 'website_checks') }}
where domain is not null
