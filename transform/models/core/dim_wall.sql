-- One row per hitting wall. Blank flags stay NULL (unknown); `confirmation` says how we know (reported / official).
select * from {{ ref('stg_manual_walls') }}
