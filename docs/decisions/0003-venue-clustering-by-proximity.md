# ADR 0003: Cluster courts into venues by proximity, in portable SQL

**Status:** accepted (naming is still a known gap)

## Context
ADR 0002 found that OpenStreetMap maps individual courts, so a 12-court club looks like 12 unrelated points.
Users search for places, not courts.

## Decision
Treat courts within **75 m** of each other as one facility (`venue_radius_m`, a dbt var).
- `int_court_pairs`: all court pairs within the radius (cheap lat/lon box filter first, then exact distance).
- `int_court_clusters`: connected components via iterative minimum-label propagation, written as plain SQL
  (8 unrolled passes) so it runs identically on DuckDB and Snowflake. No recursive CTE, no UDF, no Python.
- `assert_clusters_converged` proves 8 passes were enough; if data changes and a cluster is still moving, the test fails.
- `dim_venue` rolls courts up; on Snowflake it also adds a `GEOGRAPHY` column for `ST_DWITHIN` / `ST_DISTANCE`.

## Result (LA extract)
| | Before | After |
|---|---|---|
| Records the user would browse | 3,253 courts | **1,354 venues** |
| Venues with 9+ courts (clubs, parks) | not visible | 54 |
| Venues with a usable name | 23 | 23 |

## Known gap
Clustering fixed the *count* but not the *names*: 1,331 of 1,354 venues are still unnamed, because the names live on
parent features (parks, club polygons) and in places data that we don't join yet. Roughly 760 venues are a single court,
many of them residential and not bookable.

## Alternatives considered
- **Grid / geohash buckets:** simple, but splits a facility that straddles a cell edge.
- **DBSCAN in Python:** fine on a laptop, but not portable to Snowflake SQL models, and harder to test.
- **Recursive CTE:** works on both engines but is harder to reason about and to bound.

## Next
Join OSM parent features (park / club polygons) and a Places API for names, hours and booking links; tune the radius using a hand-labelled sample.
