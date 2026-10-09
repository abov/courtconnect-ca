{# Small adapter shims so the same model runs on DuckDB (local) and Snowflake (cloud). #}

{% macro regex_extract(col, pattern) %}
  {{ return(adapter.dispatch('regex_extract', 'courtconnect')(col, pattern)) }}
{% endmacro %}

{% macro default__regex_extract(col, pattern) -%}
  regexp_substr({{ col }}, '{{ pattern }}', 1, 1, 'e', 1)
{%- endmacro %}

{% macro duckdb__regex_extract(col, pattern) -%}
  nullif(regexp_extract({{ col }}, '{{ pattern }}', 1), '')
{%- endmacro %}

{# Parse strings like '3ft', '34in', '2ft 11in', '5ft 7in / 5ft 11in' into inches (first value wins). #}
{% macro to_inches(col) %}
  case
    when {{ col }} is null then null
    else coalesce(try_cast({{ regex_extract(col, '([0-9.]+)ft') }} as double), 0) * 12
       + coalesce(try_cast({{ regex_extract(col, '([0-9.]+)in') }} as double), 0)
  end
{% endmacro %}

{# Lowercase, non-alphanumerics -> single spaces, padded with spaces: ' pacific beach tennis club '.
   Lets us match whole words/phrases with  LIKE '% term %'  on both engines. #}
{% macro normalize_name(col) %}
  {{ return(adapter.dispatch('normalize_name', 'courtconnect')(col)) }}
{% endmacro %}

{% macro default__normalize_name(col) -%}
  ' ' || trim(regexp_replace(lower({{ col }}), '[^a-z0-9]+', ' ')) || ' '
{%- endmacro %}

{% macro duckdb__normalize_name(col) -%}
  ' ' || trim(regexp_replace(lower({{ col }}), '[^a-z0-9]+', ' ', 'g')) || ' '
{%- endmacro %}
