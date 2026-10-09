# Architecture

```
Google Sheet (master sports list) ─┐
OpenStreetMap courts (Overpass) ───┼─► RAW ─► STAGING ─► INTERMEDIATE ─► CORE ─► MARTS ─► app / dashboard
OpenStreetMap parks, schools, clubs┘  (landing) (clean)   (graph, joins)  (dims)  (what users read)
   extract / sync (Python)            load (idempotent)        dbt: tests, docs, lineage
```

| Layer | Objects | Purpose |
|---|---|---|
| raw | `osm_courts`, `osm_parents`, `all_racquet`, `osm_sport_map`, `sport_aliases` | Untouched source data. `all_racquet` is synced from the Google Sheet. |
| staging | `stg_sports`, `stg_osm_courts`, `stg_osm_parents` | Typed, standardised, de-duplicated. Surface and indoor/outdoor derived here. |
| intermediate | `int_court_pairs`, `int_court_clusters`, `int_court_parent` | Proximity graph, venue clustering, enclosing park / school / club |
| core | `dim_sport`, `dim_court`, `dim_venue`, `bridge_court_sport` | Business entities |
| marts | `mart_venue_finder`, `mart_court_finder`, `mart_sport_coverage`, `mart_sport_surface_coverage`, `mart_sport_gaps` | What the app and dashboards read |

- `mart_venue_finder`: one row per (venue, sport), with surfaces, indoor/outdoor, address and website.
- `mart_court_finder`: one row per (court, sport), for drawing individual courts on a map.
- `mart_sport_gaps`: every sport with an honest status (`covered`, `sparse`, `tagged_none_found`, `no_osm_tag`) and the next source to try.

Environments: **DuckDB** (local dev, CI) and **Snowflake** (cloud), identical results. See ADR 0001.
CI loads a small real-data sample (`ci/fixtures`) and builds and tests the whole project.

Decisions: [`docs/decisions`](decisions). Coverage: [`coverage_snapshot.md`](coverage_snapshot.md). Sports we cannot find: [`sport_name_review.md`](sport_name_review.md).

Planned: S3 landing + Snowpipe, Terraform, a second data source (Places / club directories), events and ticketing, synthetic social layer.
