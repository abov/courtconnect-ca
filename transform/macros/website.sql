{# Reduce a website to its bare domain: 'HTTPS://www.Example.com:8080/a?b#c' -> 'example.com'.
   MUST stay in step with domain_of() in ingestion/check_websites.py, or checked domains will not join back.
   Plain string functions only (no regex), so it behaves the same on DuckDB and Snowflake. #}
{% macro website_domain(col) -%}
  case
    when {{ col }} is null or trim({{ col }}) = '' then null
    when split_part(split_part(split_part(split_part(replace(replace(lower(trim({{ col }})), 'https://', ''), 'http://', ''), '/', 1), '?', 1), '#', 1), ':', 1) like 'www.%'
      then substr(split_part(split_part(split_part(split_part(replace(replace(lower(trim({{ col }})), 'https://', ''), 'http://', ''), '/', 1), '?', 1), '#', 1), ':', 1), 5)
    else split_part(split_part(split_part(split_part(replace(replace(lower(trim({{ col }})), 'https://', ''), 'http://', ''), '/', 1), '?', 1), '#', 1), ':', 1)
  end
{%- endmacro %}

{# ok / dead / unknown from the website check; 'unchecked' when we have a website but no check row yet; null when no website. #}
{% macro website_status(website_col, status_col) -%}
  case
    when {{ website_col }} is null or trim({{ website_col }}) = '' then null
    when {{ status_col }} is null then 'unchecked'
    else {{ status_col }}
  end
{%- endmacro %}
