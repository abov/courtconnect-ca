{# Straight-line distance in miles between two lat/lon points (flat-earth approximation, same as the metre formulas in int_court_pairs;
   fine under ~100 miles). Not a drive time. #}
{% macro distance_mi(lat1, lon1, lat2, lon2) -%}
    (sqrt(power(({{ lat1 }} - {{ lat2 }}) * 110540, 2)
        + power(({{ lon1 }} - {{ lon2 }}) * cos(radians({{ lat1 }})) * 111320, 2)) / 1609.344)
{%- endmacro %}
