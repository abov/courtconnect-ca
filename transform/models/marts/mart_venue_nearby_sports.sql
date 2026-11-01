-- "Try another sport": for each venue, the racket sports it is NOT listed for that are available at other venues within 15 miles
-- (straight-line), with how many and the nearest one. A sport missing from a venue's rows has nothing within 15 miles in our data,
-- which can also mean the sport is under-mapped (see mart_sport_gaps). INFERRED.
select
    p.venue_id,
    p.sport_name,
    count(distinct p.other_venue_id)                                       as venues_within_15mi,
    count(distinct case when p.dist_mi <= 5 then p.other_venue_id end)     as venues_within_5mi,
    round(min(p.dist_mi), 2)                                               as nearest_mi,
    'inferred'                                                             as confirmation
from {{ ref('int_venue_pairs_15mi') }} p
where not exists (
    select 1
    from {{ ref('mart_venue_neighbors') }} n
    where n.venue_id = p.venue_id and n.sport_name = p.sport_name
)
group by 1, 2
