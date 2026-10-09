{{ config(severity='warn') }}
-- The platform should cover every racket sport on the sheet (expected: 76).
-- Warns (does not fail) if the count differs, so a gap in the sheet is visible rather than silent.
select count(*) as sports_found, {{ var('expected_racket_sports') }} as sports_expected
from {{ ref('dim_sport') }}
where sport_family like 'Racket%'
having count(*) <> {{ var('expected_racket_sports') }}
