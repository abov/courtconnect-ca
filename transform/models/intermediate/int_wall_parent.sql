-- For each hitting-wall pin, the smallest NAMED feature (park, school, club...) whose bounding box contains it: the same pick and grid join as
-- int_court_parent, for walls. Used to name a wall venue after the place it stands in (name_source 'enclosing_feature': inferred from the
-- bounding box, never a confirmed name). Golf courses, resorts and hotels only when nothing else contains the wall.
{% set cell = 0.02 %}
with parent_cells as (
    select p.*, y.cy, x.cx
    from {{ ref('stg_osm_parents') }} p,
         unnest(generate_series(cast(floor(p.minlat / {{ cell }}) as bigint), cast(floor(p.maxlat / {{ cell }}) as bigint))) as y(cy),
         unnest(generate_series(cast(floor(p.minlon / {{ cell }}) as bigint), cast(floor(p.maxlon / {{ cell }}) as bigint))) as x(cx)
),

matches as (
    select
        w.wall_key,
        p.parent_id,
        p.parent_name,
        p.kind_group,
        p.bbox_area_deg2,
        row_number() over (
            partition by w.wall_key
            order by case when p.kind_group = 'resort_or_other' then 2 else 1 end,
                     p.bbox_area_deg2 asc, p.parent_id
        ) as rn
    from {{ ref('mart_wall_pins') }} w
    join parent_cells p
      on p.cy = cast(floor(w.lat / {{ cell }}) as bigint)
     and p.cx = cast(floor(w.lon / {{ cell }}) as bigint)
     and w.lat between p.minlat and p.maxlat
     and w.lon between p.minlon and p.maxlon
)

select wall_key, parent_id, parent_name, kind_group as parent_kind, bbox_area_deg2 as parent_area
from matches
where rn = 1
