-- Fails when two racket vacation rows sit within 300 m of each other and share a sport, so one resort listed
-- twice (an own page and a directory) cannot become two pins. Fix: merge the rows, keep the provider's own page.
-- If they really are different offers at one place, add the pair to `reviewed`.
with reviewed(a, b) as (
    values ('none-yet', 'none-yet-either')
)
select x.vacation_key as vacation_a, y.vacation_key as vacation_b, 'possible duplicate vacation (same place, shared sport)' as problem
from {{ ref('stg_racket_vacations') }} x
join {{ ref('stg_racket_vacations') }} y
  on x.vacation_key < y.vacation_key
 and sqrt(power((x.lat - y.lat) * 111.0, 2) + power((x.lon - y.lon) * 111.0 * cos(radians(x.lat)), 2)) < 0.3
 and len(list_intersect(string_split(x.sports, ';'), string_split(y.sports, ';'))) > 0
where not exists (
    select 1 from reviewed r
    where (r.a = x.vacation_key and r.b = y.vacation_key) or (r.a = y.vacation_key and r.b = x.vacation_key)
)
