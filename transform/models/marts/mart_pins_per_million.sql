-- Supply per capita, one row per (region, sport) plus an 'All sports' row per region. A stand-in for search interest where Google Trends has no data
-- (Trends covers CA + NV only; owner 2026-11-24). It measures how many pins we list per million people, NOT how many people want to play.
-- Population is the region's 2020 census count (seed region_population: state/country level, not metro). One pin = one venue per sport,
-- so a venue with two sports counts once in each sport row and once in the 'All sports' row. Sports that are only "also played" are left out,
-- as in mart_search_vs_coverage. Planning signal only: not shown in the app.
with pins as (
    select region, sport_name, count(distinct venue_id) as pins
    from {{ ref('mart_venue_finder') }}
    where lat is not null
      and sport_name not in (select trim(also_sport) from {{ ref('sport_also_played') }})
    group by 1, 2
),

all_sports as (
    select region, count(distinct venue_id) as pins
    from {{ ref('mart_venue_finder') }}
    where lat is not null
      and sport_name not in (select trim(also_sport) from {{ ref('sport_also_played') }})
    group by 1
),

rows_ as (
    select region, sport_name, pins, false as is_total from pins
    union all
    select region, 'All sports', pins, true from all_sports
)

select
    r.region,
    r.sport_name,
    r.is_total,
    r.pins,
    p.population,
    p.year as population_year,
    round(r.pins * 1000000.0 / p.population, 1) as pins_per_million
from rows_ r
join {{ ref('region_population') }} p on p.region = r.region
