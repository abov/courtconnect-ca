-- Fails if any court's venue label was still changing on the final pass,
-- which would mean the clustering needs more passes (raise `passes` in int_court_clusters).
select court_id from {{ ref('int_court_clusters') }} where changed_in_last_pass
