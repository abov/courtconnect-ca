# CourtConnect California

**Find where to play, who to play with, and where to watch, for every racket sport in California.**

> Plain-English summary: Pickleball, padel, tennis, squash, and 40+ lesser-known racket sports
> are booming, but information about *where to play* is scattered and messy. This project collects
> it, cleans it, checks it, and tells you honestly how complete it is.

## What works today (Phase 1)
- A cleaned reference list of **46 racket sports** (from a hand-built spreadsheet full of typos and mixed units, now typed and validated)
- **3,253 real court records for Los Angeles** pulled from OpenStreetMap, grouped into **1,354 venues** by proximity (a 28-court club is one row, not 28)
- A **coverage report**: venues and courts per sport, how many are confirmed public, how many still lack a name
- **34 automated checks** (all passing) that catch bad data before anyone sees it
- The same project runs on **local DuckDB and Snowflake** with identical results, including a geospatial search ("padel within 12 miles of downtown")

## 60-second demo
```bash
pip install -r requirements.txt
make demo      # extract -> load -> build -> test
```
Then open `courtconnect.duckdb` and query `marts.mart_sport_coverage`.

**The story to tell:** *"Here's the messy spreadsheet; here's the clean table. Here's LA: 3,253 anonymous map points became 1,354 places, but only 23 have names, so I built the coverage report to show that gap instead of hiding it."*

## For engineers
- dbt project runs unchanged on **DuckDB (dev/CI)** and **Snowflake** via `adapter.dispatch` macros
- Idempotent loads, dbt tests (unique, not-null, accepted values, relationships, custom geo-bounds test)
- Source freshness check, Snowflake resource monitor + least-privilege role (`infra/snowflake/00_setup.sql`)
- Architecture decisions in [`docs/decisions`](docs/decisions); layout in [`docs/architecture.md`](docs/architecture.md)

## Run on Snowflake
1. Run `infra/snowflake/00_setup.sql` in Snowsight as ACCOUNTADMIN
2. `cp .env.example .env` and add your credentials
3. `make snowflake-build`

## Roadmap
- [x] `dim_venue`: cluster individual courts into facilities ([ADR 0003](docs/decisions/0003-venue-clustering-by-proximity.md))
- [ ] Venue names: join park/club polygons and a Places API (1,331 of 1,354 venues are still unnamed)
- [ ] Statewide extract, S3 landing zone, Snowpipe, Terraform
- [ ] Events and ticketing (pro/amateur matches, watch parties)
- [ ] Synthetic social layer (groups, sessions) with PII masking policies
- [ ] Map app / Streamlit front end
