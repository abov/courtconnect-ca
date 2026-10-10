-- A venue action must point at a venue we hold, link out over https, and have sane dates.
select action_key, 'venue not found' as problem from {{ ref('stg_venue_actions') }} where venue_id is null
union all
select action_key, 'link is not https' from {{ ref('stg_venue_actions') }} where url is null or url not like 'https://%'
union all
select action_key, 'end before start' from {{ ref('stg_venue_actions') }} where start_date is not null and end_date is not null and end_date < start_date
union all
select action_key, 'action_key not unique'
from {{ ref('stg_venue_actions') }} group by action_key having count(*) > 1
