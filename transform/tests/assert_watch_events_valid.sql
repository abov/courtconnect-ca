-- Fails on a watch event that is internally inconsistent or unsafe to show:
--  * coordinates outside California (typo)         * end before start
--  * a "confirmed" date with no dates              * links that are not https
select event_key, 'bad coordinates' as problem from {{ ref('stg_watch_events') }}
where lat is null or lon is null or lat not between 32.5 and 42.1 or lon not between -124.5 and -114.1
union all
select event_key, 'end before start' from {{ ref('stg_watch_events') }}
where start_date is not null and end_date is not null and end_date < start_date
union all
select event_key, 'confirmed but missing dates' from {{ ref('stg_watch_events') }}
where date_status = 'confirmed' and (start_date is null or end_date is null)
union all
select event_key, 'link is not https' from {{ ref('stg_watch_events') }}
where (info_url is not null and info_url not like 'https://%') or (tickets_url is not null and tickets_url not like 'https://%')
union all
select event_key, 'no official link' from {{ ref('stg_watch_events') }}
where info_url is null and tickets_url is null
