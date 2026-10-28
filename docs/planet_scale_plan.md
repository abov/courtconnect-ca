# Planet-scale read: Overture benchmark (plan)

**Goal:** show, with measured numbers, that the pipeline reads a planet-scale source (Overture, hundreds of GB on S3) and touches only the CA+NV slice. No claim goes in the README until the benchmark has run.

## What exists
`extract_overture_places.py` and `extract_overture_addresses.py` already read the full release from S3 with DuckDB (`read_parquet('s3://overturemaps-us-west-2/release/<r>/theme=.../*', hive_partitioning=1)`) and filter on `bbox.xmin/ymin` (CA+NV box) and category. Nothing measures how little of the release that actually reads.

## Scope (one session, no spend, no new dependencies)
1. `ingestion/oneoff/overture_scale_benchmark.py` (outside `make`, like other one-off scans), for `places` and `addresses` (optionally `buildings` as the largest theme):
   - **Release size:** sum object sizes per theme via S3 `ListObjectsV2` (public bucket, same unauthenticated style as `latest_release()`).
   - **Rows:** planet total (`count(*)` is answered from parquet footers) vs CA+NV bbox vs kept.
   - **Bytes read:** HTTP bytes DuckDB fetched for the real extract query (use DuckDB's HTTP logging/profiling; verify which setting this DuckDB version has) vs release size = % scanned.
   - **Wall-clock** for the same query.
2. Write results to `docs/planet_scale_benchmark.md` (release id, date, machine, numbers). Re-run on a new release only when asked.
3. README: one short "Scale" paragraph quoting only those measured numbers and linking the doc.

## Rules
- Report what was measured, labelled with release id. Do not quote Overture's published sizes from memory.
- Same User-Agent / no personal contact rule applies (the S3 listing sends none).
- If bytes-read cannot be measured reliably, say so in the doc and report release size, rows and runtime only.

## Out of scope (next, if wanted)
- OSM minutely replication diffs filtered to CA/NV racket tags -> `app/data/changes.json` (ADR 0025 step 1). Own ADR first.
- Overture release-to-release diff (new/closed places) into the same changes feed.
- NAIP stays dropped (`docs/ml_plan.md`).
