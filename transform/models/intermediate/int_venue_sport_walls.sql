-- Sports a hitting wall supports, per venue (ADR 0032): a wall pin counts for the court venue it links to, else for its own wall venue.
-- The sports come from the wall's type (seeds/wall_type_sports.csv): INFERRED from the structure, never confirmed play. `courts` is the
-- number of walls. A type the seed does not list (the unchecked "handball-type" walls) supports nothing; public_only sports (Knuckle
-- Racket) need the wall marked public.
with pins as (
    select
        w.wall_key,
        coalesce(l.venue_id, md5('wall:' || w.wall_key)) as venue_id,
        w.wall_count,
        w.access,
        unnest(string_split(w.wall_type, ';'))           as wall_type
    from {{ ref('mart_wall_pins') }} w
    left join {{ ref('int_wall_venue_link') }} l on l.wall_key = w.wall_key
)

select
    p.venue_id,
    s.sport_id,
    sum(p.wall_count)::integer as courts
from pins p
join {{ ref('wall_type_sports') }} t on t.wall_type = p.wall_type
join {{ ref('dim_sport') }} s on s.sport_name = t.sport
where lower(trim(coalesce(t.public_only, ''))) <> 'yes' or p.access = 'public'
group by 1, 2
