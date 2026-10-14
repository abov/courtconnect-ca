-- Sanity checks on the physical sport-fit reference. Returns rows only for violations.
select 'tennis should host pickleball' as failed_check
where not exists (select 1 from {{ ref('ref_sport_fit') }} where host_sport = 'Tennis' and guest_sport = 'Pickleball')
union all
select 'pickleball must not host tennis'
where exists (select 1 from {{ ref('ref_sport_fit') }} where host_sport = 'Pickleball' and guest_sport = 'Tennis')
union all
select 'a sport must not host itself'
where exists (select 1 from {{ ref('ref_sport_fit') }} where host_sport = guest_sport)
