-- Which sports a place offers, and how good the evidence is.
--   category          : Overture itself classifies it as a racket sport venue            -> strong
--   name_keyword      : a sport word appears in the business name
--        distinctive term ("padel", "squash", "table tennis" ...)                           -> strong
--        ambiguous term  ("real tennis" also matches "Camino Real Tennis Center")           -> weak (never counted as a venue)
with category_matches as (
    select p.place_id, s.sport_id, 'category' as match_type, p.category as matched_term, 'strong' as evidence
    from {{ ref('stg_overture_places') }} p
    join {{ ref('overture_category_map') }} m on m.overture_category = p.category
    join {{ ref('dim_sport') }} s on s.sport_name = m.sport
),

name_matches as (
    select p.place_id, s.sport_id, 'name_keyword' as match_type, t.term as matched_term,
           case when t.reliability = 'distinctive' then 'strong' else 'weak' end as evidence
    from {{ ref('stg_overture_places') }} p
    join {{ ref('sport_search_terms') }} t on p.name_norm like '% ' || t.term || ' %'
    join {{ ref('dim_sport') }} s on s.sport_name = t.sport
),

-- "Table Tennis Association" must not also count as plain "Tennis": drop a name match when a longer
-- matched term for the same place contains it.
name_matches_specific as (
    select a.*
    from name_matches a
    where not exists (
        select 1 from name_matches b
        where b.place_id = a.place_id
          and length(b.matched_term) > length(a.matched_term)
          and b.matched_term like '%' || a.matched_term || '%'
    )
),

-- Overture's category is dropped when the place's own name clearly says another sport: the name has a distinctive term for a
-- different sport ("table tennis" on a tennis_court) and, once that term is removed, no standalone word of the category sport is
-- left ("Anaheim Tennis and Pickleball Center" keeps Tennis; "Ararat Table Tennis" loses it). Ambiguous terms ("beach tennis") never
-- trigger this (Newport Beach Tennis Club is a real tennis club): use place_sport_overrides.csv for those.
-- "tennis", "racquet club" and "racket club" are generic (multi-sport tennis centres are common, and a pickleball_court inside a
-- "Tennis Center" is real), so they never contradict a category.
category_name_conflicts as (
    select distinct c.place_id, c.sport_id
    from category_matches c
    join {{ ref('stg_overture_places') }} p on p.place_id = c.place_id
    join {{ ref('dim_sport') }} cs on cs.sport_id = c.sport_id
    join name_matches_specific n on n.place_id = c.place_id
         and n.evidence = 'strong' and n.sport_id <> c.sport_id
         and n.matched_term not in ('tennis', 'racquet club', 'racket club')
    where not exists (
        select 1
        from {{ ref('sport_search_terms') }} own
        where trim(own.sport) = cs.sport_name
          and replace(p.name_norm, ' ' || n.matched_term || ' ', ' ') like '% ' || own.term || ' %'
    )
),

category_kept as (
    select c.*
    from category_matches c
    left join category_name_conflicts x on x.place_id = c.place_id and x.sport_id = c.sport_id
    where x.place_id is null
),

unioned as (
    select * from category_kept
    union all
    select * from name_matches_specific
),

ranked as (
    select *,
           row_number() over (
               partition by place_id, sport_id
               order by case evidence when 'strong' then 1 else 2 end, case match_type when 'category' then 1 else 2 end, matched_term
           ) as rn
    from unioned
),

base as (
    select place_id, sport_id, match_type, matched_term, evidence
    from ranked
    where rn = 1
),

-- Human review (seeds/place_sport_overrides.csv): verdict 'confirm' makes the match strong, 'reject' removes it.
overrides as (
    select o.place_id, s.sport_id, lower(trim(o.verdict)) as verdict
    from {{ ref('place_sport_overrides') }} o
    join {{ ref('dim_sport') }} s on s.sport_name = trim(o.sport)
),

kept as (
    select b.*
    from base b
    left join overrides o on o.place_id = b.place_id and o.sport_id = b.sport_id
    where o.place_id is null
),

confirmed as (
    select place_id, sport_id, 'manual' as match_type, 'confirmed in review' as matched_term, 'strong' as evidence
    from overrides
    where verdict = 'confirm'
),

settled as (
    select * from kept
    union all
    select * from confirmed
),

-- A place that offers sport A also offers sport B where sport_also_played.csv says so (racquetball courts host 4-wall paddle).
-- The derived row keeps the evidence strength of the row it comes from, and its matched_term says why it is there.
also_played as (
    select s.place_id, d.sport_id, 'also_played' as match_type,
           'also played on ' || lower(trim(a.sport)) || ' courts' as matched_term, s.evidence
    from settled s
    join {{ ref('dim_sport') }} f on f.sport_id = s.sport_id
    join {{ ref('sport_also_played') }} a on trim(a.sport) = f.sport_name
    join {{ ref('dim_sport') }} d on d.sport_name = trim(a.also_sport)
    join {{ ref('stg_overture_places') }} p on p.place_id = s.place_id
    where not exists (select 1 from settled x where x.place_id = s.place_id and x.sport_id = d.sport_id)
      -- exclude_name_inferred = yes: the place's sport came from its name (name_keyword), not from an Overture category or a human
      -- confirmation, so the sport is not passed on; only known (tagged or confirmed) courts count
      and not (lower(trim(coalesce(a.exclude_name_inferred, ''))) = 'yes' and s.match_type = 'name_keyword')
      -- exclude_private_members = yes: Overture has no access tag, so a club-style name (country / athletic / racquet / tennis / golf /
      -- swim club, "private", "members") counts as private or members-only and does not pass the sport on
      and not (lower(trim(coalesce(a.exclude_private_members, ''))) = 'yes'
               and (p.name_norm like '% country club %' or p.name_norm like '% athletic club %' or p.name_norm like '% racquet club %'
                    or p.name_norm like '% tennis club %' or p.name_norm like '% golf club %' or p.name_norm like '% swim club %'
                    or p.name_norm like '% private %' or p.name_norm like '% members %'))
)

select * from settled
union all
select * from also_played
