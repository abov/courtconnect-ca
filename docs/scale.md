# Scale: what the pipeline reads and how it grows

Two measured checks in one place. Part 1 is how little of a planet-scale source the extracts read. Part 2 is how the build time grows when the data does. (Merged 2026-11-12 from `planet_scale_benchmark.md`, `planet_scale_plan.md` and `scaling.md`.)

## 1. Planet-scale read: Overture benchmark

Measured 2026-10-28 on Overture release `2026-10-21.0`, DuckDB 1.5.6, Windows AMD64, 8 threads, home internet. Script: `ingestion/oneoff/overture_scale_benchmark.py`; raw numbers: `docs/planet_scale_benchmark.json`.

The two real extracts (`extract_overture_places.py`, `extract_overture_addresses.py`) read the public Overture parquet on S3 with DuckDB range requests. They filter on the CA+NV bounding box and fetch only the byte ranges they need, so a laptop never downloads the planet.

## Results

- **Places:** 16 files, 11.9 GB, 88.4M rows planet-wide. The extract query returned 95,752 rows (before the name/border filter in Python), fetched 289 MB (2.4% of the theme) in 2,670 requests, 50 s.
- **Addresses:** 64 files, 27.7 GB, 475.3M rows. The extract query (address points within one cell of a pin) returned 5.29M rows, fetched 454 MB (1.6% of the theme) in 3,148 requests, 50 s.
- **Buildings (size and row count only, not used by the pipeline):** 512 files, 276.9 GB, 2.53B rows. Counting rows from the parquet footers read 543 MB (0.2%) in 253 s.
- **Three themes together:** 316.5 GB on S3, of which the extracts fetched about 743 MB.

## What this does and does not show

- It shows a pipeline that queries a hundreds-of-GB columnar source in place and pays for about 2% of it. The data we keep is small (a few thousand venues).
- It is not terabyte processing, and the whole Overture release has more themes than the three measured here. Nothing here is streaming; for that see the OSM replication idea under "Not built" below.
- Bytes are the sum of `Content-Length` on every HTTP GET DuckDB logged during the step; retried requests would count twice. The address count depends on the pins in the shared `data/raw` at run time, so it will differ from the last real extract.
- Overture keeps a release about 60 days, so re-running on this release id will eventually fail; omit `--release` to use the newest.

Script: `ingestion/oneoff/overture_scale_benchmark.py` (outside `make`; reads only, writes nothing to `data/raw`). Re-run on a new release only when asked. Rule: report what was measured, labelled with the release id; never quote Overture's published sizes from memory.

## 2. Scaling benchmark (2026-11-02)

`python ingestion/bench_scale.py 1 3 10` copies the DuckDB, replicates the OSM and Overture raw tables N times (each copy shifted on a lat/lon grid so copies never overlap), then times `dbt run`. Seeds stay at 1x, tests are skipped. Machine: 32 GB RAM, laptop, 4 dbt threads.

| Scale | Address rows | `dbt run` | Peak memory | Mart venues | Slowest model |
|---|---|---|---|---|---|
| 1x | 5.3 M | 2.2 min | 5.3 GB | 48 k | `int_venue_address` 34 s |
| 3x | 15.9 M | 15.4 min | 14.8 GB | 140 k | `int_court_parent` 367 s |
| 10x | 53.0 M | 158 min | 13.4 GB | 463 k | `int_court_parent` 3,302 s |

### What it shows
- **It runs at 10x on one laptop, no Spark needed.** The build finished with 13 GB peak (DuckDB spills to disk), but it took 2.6 hours.
- **Time grows about quadratically**: 3x data = 7x time, 10x data = 72x time. `int_court_parent` went 31 s to 3,302 s (106x), `int_venue_address` 34 s to 2,078 s (61x). Replicas sit far apart, so a join that pruned by location would stay linear. This points to nearby-point joins that compare every pair (inference: the model SQL was not read for this note).
- **Likely fix** (not done): bucket points by grid cell or region before joining, so cost is per cell. Worth trying before any new engine.
- **Browser payload**: the real `app/data/venues.json` is about 2.2 MB for about 10k venues, so it grows roughly 0.2 MB per 1k venues. Around 50 k venues (5 states) is about 10 MB, where vector tiles or PMTiles start to pay off.
- **Caveat**: "Mart venues" counts every `mart_venue_finder` row, not the exported subset; the old payload column measured that table and is not `venues.json`.

### Next
Profile `int_court_parent` and `int_venue_address` and add grid bucketing, then rerun at 3x. Compare against a PySpark version only if it is still slow.

## Not built (ideas, no work planned)
- OSM minutely replication diffs filtered to CA/NV racket tags, written to `app/data/changes.json` (ADR 0025 step 1; needs its own ADR first, see ADR 0026).
- An Overture release-to-release diff (new and closed places) into the same changes feed.
- NAIP imagery stays dropped (`docs/ml_plan.md`).
