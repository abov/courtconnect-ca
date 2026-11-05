-- Racket sport vacations the map may show: verified rows only (ADR 0036). A discovery list; every row links out to the provider.
-- One row per offer; `sports` is the offer's semicolon list, each name checked against dim_sport by assert_racket_vacations_valid.
select
    v.vacation_id,
    v.vacation_name,
    v.kind,
    v.destination,
    v.country,
    v.lat,
    v.lon,
    v.sports,
    v.who_can_play,
    v.price_note,
    v.info_url,
    v.evidence,
    v.verified_on
from {{ ref('stg_racket_vacations') }} v
where v.status = 'verified'
