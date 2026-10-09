select court_id from {{ ref('dim_court') }} where venue_id is null
union all
select 'venue_court_total_mismatch'
where (select sum(court_records + facility_records) from {{ ref('dim_venue') }}) <> (select count(*) from {{ ref('dim_court') }})
