-- For each court/facility, the smallest NAMED feature (park, school, club...) whose bounding box contains it.
-- Bounding boxes over-cover irregular shapes, so this is an approximation: it is labelled as
-- 'enclosing_feature' downstream, never as a confirmed court name. Golf courses, resorts and hotels have big
-- irregular bounding boxes that swallow nearby courts, so they are used only when nothing else contains the court.
with matches as (
    select
        c.court_id,
        p.parent_id,
        p.parent_name,
        p.kind_group,
        p.bbox_area_deg2,
        row_number() over (
            partition by c.court_id
            order by case when p.kind_group = 'resort_or_other' then 2 else 1 end,   -- golf courses / hotels only as a last resort
                     p.bbox_area_deg2 asc, p.parent_id
        ) as rn
    from {{ ref('stg_osm_courts') }} c
    join {{ ref('stg_osm_parents') }} p
      on c.lat between p.minlat and p.maxlat
     and c.lon between p.minlon and p.maxlon
)

select court_id, parent_id, parent_name, kind_group as parent_kind, bbox_area_deg2 as parent_area
from matches
where rn = 1
