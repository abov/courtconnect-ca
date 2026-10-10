-- Things to do at each venue, with the provider's link. Link-outs only: the provider (not CourtConnect) takes any registration or payment.
select
    a.action_key,
    a.venue_id,
    v.venue_name,
    v.city,
    a.action_type,
    a.title,
    a.provider,
    a.url,
    a.price_info,
    a.start_date,
    a.end_date,
    (a.end_date is null or a.end_date >= current_date)        as is_current,
    a.evidence,
    a.verified_on
from {{ ref('stg_venue_actions') }} a
join {{ ref('dim_venue') }} v on v.venue_id = a.venue_id
