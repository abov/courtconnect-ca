-- A confirmation must point at a hand-added venue, carry a date and evidence, and use a handle (not an email or a spaced name).
select c.venue_key, 'venue not in manual_venues' as problem
from {{ ref('stg_venue_confirmations') }} c left join {{ ref('stg_manual_venues') }} m on m.venue_key = c.venue_key
where m.venue_key is null
union all
select venue_key, 'missing date or evidence' from {{ ref('stg_venue_confirmations') }} where confirmed_on is null or evidence is null
union all
select venue_key, 'confirmed_by must be a GitHub handle' from {{ ref('stg_venue_confirmations') }}
where confirmed_by like '%@%' or confirmed_by like '% %'
union all
select venue_key, 'same person, method and day twice' from {{ ref('stg_venue_confirmations') }}
group by venue_key, confirmed_by, method, confirmed_on having count(*) > 1
