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

unioned as (
    select * from category_matches
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
)

select * from kept
union all
select * from confirmed
