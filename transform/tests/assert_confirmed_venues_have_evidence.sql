-- A hand-added venue marked visited or official must say how we know (evidence). A visited row also needs the date of the visit.
select venue_key, sport_name, 'confirmed without evidence' as problem
from {{ ref('stg_manual_venues') }}
where confirmation_level in ('visited', 'official') and evidence is null
union all
select venue_key, sport_name, 'visited without a date'
from {{ ref('stg_manual_venues') }}
where confirmation_level = 'visited' and confirmed_on is null
