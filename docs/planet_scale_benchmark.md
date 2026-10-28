# Planet-scale read: Overture benchmark

Measured 2026-10-28 on Overture release `2026-10-21.0`, DuckDB 1.5.6, Windows AMD64, 8 threads, home internet. Script: `ingestion/oneoff/overture_scale_benchmark.py`; raw numbers: `docs/planet_scale_benchmark.json`. Plan: `docs/planet_scale_plan.md`.

The two real extracts (`extract_overture_places.py`, `extract_overture_addresses.py`) read the public Overture parquet on S3 with DuckDB range requests. They filter on the CA+NV bounding box and fetch only the byte ranges they need, so a laptop never downloads the planet.

## Results

- **Places:** 16 files, 11.9 GB, 88.4M rows planet-wide. The extract query returned 95,752 rows (before the name/border filter in Python), fetched 289 MB (2.4% of the theme) in 2,670 requests, 50 s.
- **Addresses:** 64 files, 27.7 GB, 475.3M rows. The extract query (address points within one cell of a pin) returned 5.29M rows, fetched 454 MB (1.6% of the theme) in 3,148 requests, 50 s.
- **Buildings (size and row count only, not used by the pipeline):** 512 files, 276.9 GB, 2.53B rows. Counting rows from the parquet footers read 543 MB (0.2%) in 253 s.
- **Three themes together:** 316.5 GB on S3, of which the extracts fetched about 743 MB.

## What this does and does not show

- It shows a pipeline that queries a hundreds-of-GB columnar source in place and pays for about 2% of it. The data we keep is small (a few thousand venues).
- It is not terabyte processing, and the whole Overture release has more themes than the three measured here. Nothing here is streaming; for that see the OSM replication idea in `docs/planet_scale_plan.md`.
- Bytes are the sum of `Content-Length` on every HTTP GET DuckDB logged during the step; retried requests would count twice. The address count depends on the pins in the shared `data/raw` at run time, so it will differ from the last real extract.
- Overture keeps a release about 60 days, so re-running on this release id will eventually fail; omit `--release` to use the newest.
