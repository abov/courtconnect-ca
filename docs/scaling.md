# Scaling benchmark (2026-11-02)

`python ingestion/bench_scale.py 1 3 10` copies the DuckDB, replicates the OSM and Overture raw tables N times (each copy shifted on a lat/lon grid so copies never overlap), then times `dbt run`. Seeds stay at 1x, tests are skipped. Machine: 32 GB RAM, laptop, 4 dbt threads.

| Scale | Address rows | `dbt run` | Peak memory | Mart venues | Slowest model |
|---|---|---|---|---|---|
| 1x | 5.3 M | 2.2 min | 5.3 GB | 48 k | `int_venue_address` 34 s |
| 3x | 15.9 M | 15.4 min | 14.8 GB | 140 k | `int_court_parent` 367 s |
| 10x | 53.0 M | 158 min | 13.4 GB | 463 k | `int_court_parent` 3,302 s |

## What it shows
- **It runs at 10x on one laptop, no Spark needed.** The build finished with 13 GB peak (DuckDB spills to disk), but it took 2.6 hours.
- **Time grows about quadratically**: 3x data = 7x time, 10x data = 72x time. `int_court_parent` went 31 s to 3,302 s (106x), `int_venue_address` 34 s to 2,078 s (61x). Replicas sit far apart, so a join that pruned by location would stay linear. This points to nearby-point joins that compare every pair (inference: the model SQL was not read for this note).
- **Likely fix** (not done): bucket points by grid cell or region before joining, so cost is per cell. Worth trying before any new engine.
- **Browser payload**: the real `app/data/venues.json` is about 2.2 MB for about 10k venues, so it grows roughly 0.2 MB per 1k venues. Around 50 k venues (5 states) is about 10 MB, where vector tiles or PMTiles start to pay off.
- **Caveat**: "Mart venues" counts every `mart_venue_finder` row, not the exported subset; the old payload column measured that table and is not `venues.json`.

## Next
Profile `int_court_parent` and `int_venue_address` and add grid bucketing, then rerun at 3x. Compare against a PySpark version only if it is still slow.
