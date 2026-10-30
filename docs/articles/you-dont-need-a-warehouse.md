# You don't need a warehouse to read a planet

*Draft, 2026-10-29. Facts come from [the Overture benchmark](../planet_scale_benchmark.md) (measured 2026-10-28, release `2026-10-21.0`), [ADR 0018](../decisions/0018-duckdb-only.md), and file sizes read from the working checkout on 2026-10-29.*

CourtConnect needs venue names and addresses from Overture Maps, a public dataset with hundreds of gigabytes of places, addresses and buildings. My first instinct was that this called for a cloud warehouse. It didn't. A single DuckDB file on a laptop read the public files in place and downloaded a small slice of them. This note shows the numbers, and where the claim stops.

## What was measured

The two real extract scripts query Overture's Parquet files on S3 with DuckDB, filter to a California and Nevada bounding box, and keep what matches. I measured them with `ingestion/oneoff/overture_scale_benchmark.py`:

- **Places:** 16 files, 11.9 GB and 88.4M rows planet-wide. The extract returned 95,752 rows before a later name filter, and fetched **289 MB (2.4% of the theme)** in 2,670 requests, about 50 s.
- **Addresses:** 64 files, 27.7 GB and 475.3M rows. The extract returned 5.29M rows and fetched **454 MB (1.6%)** in 3,148 requests, about 50 s.
- **Together:** the two extracts fetched about **743 MB of 39.6 GB** in the two themes the pipeline uses.
- **Buildings, size only:** 276.9 GB and 2.53B rows. The pipeline doesn't use them; counting rows from the file footers read 543 MB (0.2%) in 253 s.

My explanation, which the benchmark does not isolate: Parquet is columnar and stores min/max statistics per block, so DuckDB can skip blocks outside the box and fetch only the columns it needs with HTTP range requests. The measured part is the byte counts above.

## What the rest of the system weighs

- The map reads one file of **2.45 MB** with 10,288 venues.
- The raw working folder is **655 MiB**, nearly all of it one address CSV (674 MB). The DuckDB file is **494 MB**. That is not tiny, and I would not call it "a few thousand rows".
- A fresh database builds from the raw files in about a minute, and 254 dbt tests pass on it ([scorecard](../data_quality_trend.csv)).

So the shape is: a very large source, a laptop-sized working set, a small published artifact. A warehouse would have sat in the middle, doing nothing the laptop didn't already do.

## What this does not prove

- **It is not terabyte processing.** Two themes of one release, one query each. The benchmark doc says so too.
- **It is not streaming.** Each extract is a batch read. Following changes minute by minute is a different design that I sketched ([plan](../planet_scale_plan.md)) and did not build.
- **I never ran the same job on a warehouse.** I retired Snowflake for cost and upkeep ([ADR 0018](../decisions/0018-duckdb-only.md)), not because a benchmark said DuckDB was faster. I have no head-to-head number, so I make no speed claim.
- **The measurement has soft edges.** Bytes are the sum of `Content-Length` over logged GETs, so retries count twice. Timings come from one Windows machine on home internet. The address count depends on the pins loaded at run time.
- **One reader, one writer.** Nothing here shows how it behaves with concurrent users or several people writing. For those, or for data that doesn't fit on one machine, a warehouse earns its place.
- **The release will expire.** Overture keeps a release about 60 days, so the same command on the same id will eventually fail.

## What I would take from this

- **Measure the fraction you read, not the size you point at.** "743 MB of 39.6 GB" is a more useful fact than "hundreds of gigabytes".
- **Size the middle by the working set.** The source can be huge and the system small, as long as the format lets you skip most of it.
- **Say what you didn't compare.** The honest claim is "it was enough", not "it beats the alternative".
