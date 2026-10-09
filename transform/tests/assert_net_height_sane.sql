select sport_id, net_height_in
from {{ ref('dim_sport') }}
where net_height_in is not null and net_height_in not between 1 and 120
