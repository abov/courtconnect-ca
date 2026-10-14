{# Region key (ADR 0014): 'CA' or 'NV', set upstream from the state border polygon (extractors) or by hand (seeds).
   Anything else becomes null so the accepted_values test on dim_venue.region catches it. #}
{% macro region_code(col) -%}
    case upper(trim(cast({{ col }} as varchar))) when 'CA' then 'CA' when 'NV' then 'NV' end
{%- endmacro %}

{# True when a point is missing, has no region, or lies outside its region's bounding box (CA and NV boxes from
   ingestion/overpass.py REGIONS). A sanity check only: the boxes overlap near Tahoe, the extract's border polygon is the real filter. #}
{% macro outside_region_bbox(lat, lon, region) -%}
    ({{ lat }} is null or {{ lon }} is null or {{ region }} is null
     or not (({{ region }} = 'CA' and {{ lat }} between 32.5 and 42.1 and {{ lon }} between -124.5 and -114.0)
          or ({{ region }} = 'NV' and {{ lat }} between 35.0 and 42.0 and {{ lon }} between -120.01 and -114.03)))
{%- endmacro %}
