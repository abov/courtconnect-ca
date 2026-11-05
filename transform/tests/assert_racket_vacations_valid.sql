-- Fails on a racket vacation row that is internally inconsistent or unsafe to show:
--  * coordinates outside every covered region (typo)      * a sport that is not in the sport list
--  * a verified row with no evidence, date or https link   * a link that is not https
select vacation_key, 'bad coordinates' as problem from {{ ref('stg_racket_vacations') }}
where {{ outside_all_region_bboxes('lat', 'lon') }}
union all
select vacation_key, 'unknown sport: ' || trim(s.sport)
from (select vacation_key, unnest(string_split(sports, ';')) as sport from {{ ref('stg_racket_vacations') }}) s
left join {{ ref('dim_sport') }} d on d.sport_name = trim(s.sport)
where d.sport_name is null
union all
select vacation_key, 'link is not https' from {{ ref('stg_racket_vacations') }}
where info_url is not null and info_url not like 'https://%'
union all
select vacation_key, 'verified row missing evidence, date or official link' from {{ ref('stg_racket_vacations') }}
where status = 'verified' and (evidence is null or verified_on is null or info_url is null)
