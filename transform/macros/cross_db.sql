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

{# Distinctive part of a normalized name (see normalize_name): generic sport/venue words and single letters removed,
   still space-padded. 'ernie j howlett park' -> ' ernie howlett ', 'fresno city college tennis courts' -> ' fresno college '.
   Used to tell whether an Overture place is named after the park/school/centre that holds an OSM court. #}
{% macro facility_key(norm_col) -%}
  {%- set words = ['the','of','and','at','tennis','pickleball','courts','court','club','center','centre','academy','lessons',
                   'complex','racquet','racquetball','sports','sport','program','table','badminton','squash','padel','park',
                   'school','high','middle','elementary','community','recreation','rec','city','family','regional','public',
                   'track','field','fields','facility','facilities','athletic','athletics'] + ('abcdefghijklmnopqrstuvwxyz' | list) -%}
  {%- set ns = namespace(expr=norm_col) -%}
  {%- for w in words -%}{%- set ns.expr = "replace(" ~ ns.expr ~ ", ' " ~ w ~ " ', ' ')" -%}{%- endfor -%}
  {{ ns.expr }}
{%- endmacro %}

{# Street address as a comparable key: normalize_name plus common suffixes shortened ('4000 Middlefield Road' = '4000 Middlefield Rd'). #}
{% macro address_key(col) -%}
  {%- set pairs = [['road','rd'],['street','st'],['drive','dr'],['avenue','ave'],['boulevard','blvd'],['lane','ln'],['highway','hwy'],['parkway','pkwy']] -%}
  {%- set ns = namespace(expr=normalize_name(col)) -%}
  {%- for pair in pairs -%}{%- set ns.expr = "replace(" ~ ns.expr ~ ", ' " ~ pair[0] ~ " ', ' " ~ pair[1] ~ " ')" -%}{%- endfor -%}
  {{ ns.expr }}
{%- endmacro %}
