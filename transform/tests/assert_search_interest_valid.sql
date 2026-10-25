-- Search interest seed (docs/search_interest_plan.md): index is 0-100 or blank, never a made-up 0 for "no data", and every sport is a real sheet sport.
select 'out_of_range' as problem, query_geo, metro_code, sport
from {{ ref('search_interest') }}
where try_cast(index_value as double) < 0 or try_cast(index_value as double) > 100
union all
select 'zero_means_no_data', query_geo, metro_code, sport
from {{ ref('search_interest') }}
where try_cast(index_value as double) = 0
union all
select 'unknown_sport', query_geo, metro_code, sport
from {{ ref('search_interest') }}
where sport not in (select sport_name from {{ ref('dim_sport') }})
