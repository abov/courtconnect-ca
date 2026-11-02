{# Region key (ADR 0014, 0028): a state code from the `regions` var in dbt_project.yml (mirrors ingestion/regions.json; ci/check_regions.py
   fails if they differ), set upstream from the state border polygon (extractors) or by hand (seeds).
   Anything else becomes null so the accepted_values test on dim_venue.region catches it. #}
{% macro region_code(col) -%}
    case upper(trim(cast({{ col }} as varchar)))
    {%- for code in var('regions') %} when '{{ code }}' then '{{ code }}'{% endfor %} end
{%- endmacro %}

{# True when a point is missing, has no region, or lies outside its region's bounding box (the boxes in the `regions` var, same as
   ingestion/regions.json). A sanity check only: boxes can overlap near a border, the extract's border polygon is the real filter. #}
{% macro outside_region_bbox(lat, lon, region) -%}
    ({{ lat }} is null or {{ lon }} is null or {{ region }} is null
     or not (false
    {%- for code, b in var('regions').items() %}
          or ({{ region }} = '{{ code }}' and {{ lat }} between {{ b.south }} and {{ b.north }} and {{ lon }} between {{ b.west }} and {{ b.east }})
    {%- endfor %}))
{%- endmacro %}

{# True when a point is missing or lies outside every region's bounding box. #}
{% macro outside_all_region_bboxes(lat, lon) -%}
    ({{ lat }} is null or {{ lon }} is null
     or not (false
    {%- for code, b in var('regions').items() %}
          or ({{ lat }} between {{ b.south }} and {{ b.north }} and {{ lon }} between {{ b.west }} and {{ b.east }})
    {%- endfor %}))
{%- endmacro %}
