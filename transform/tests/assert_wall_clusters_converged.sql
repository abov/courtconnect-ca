-- Fails if any wall's group label was still changing on the final pass,
-- which would mean the grouping needs more passes (raise `passes` in int_wall_clusters).
select wall_key from {{ ref('int_wall_clusters') }} where changed_in_last_pass
