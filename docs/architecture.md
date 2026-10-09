# Architecture

```
OpenStreetMap (Overpass) ─┐
Sports spreadsheet (seed) ─┼─► RAW ─► STAGING ─► CORE ─► MARTS ─► app / dashboard
Ticketing + events APIs ───┘   (landing)  (clean)   (dims, bridges) (court finder, coverage)
        extract (Python)       load (idempotent)       dbt (tests + docs + lineage)
```

| Layer | Objects | Purpose |
|---|---|---|
| raw | `osm_courts`, `raw_sports`, `osm_sport_map` | Untouched source data |
| staging | `stg_sports`, `stg_osm_courts` | Typed, standardised, de-duplicated |
| core | `dim_sport`, `dim_court`, `bridge_court_sport` | Business entities |
| marts | `mart_court_finder`, `mart_sport_coverage` | What users and dashboards read |

Environments: **DuckDB** (local dev, CI) and **Snowflake** (cloud). See ADR 0001.
Planned: S3 landing + Snowpipe, Terraform, `dim_venue`, events/ticketing, synthetic social layer.
