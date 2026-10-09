# CourtConnect California

**Find where to play, who to play with, and where to watch, for every racket sport in California.**

> Plain-English summary: Pickleball, padel, tennis, squash, and 40+ lesser-known racket sports
> are booming, but information about *where to play* is scattered and messy. This project collects
> it, cleans it, checks it, and tells you honestly how complete it is.

## What works today (Phase 1)
- A cleaned reference list of **75 racket sports** (from a hand-maintained master list, full of typos and mixed units, now typed and validated). The sheet is meant to list 76; a warning test flags the gap until it does.
- **All of California from OpenStreetMap: 25,971 court and facility records, grouped into 9,490 venues** by proximity (a 28-court club is one row, not 28), for tennis, pickleball, padel, table tennis, badminton, squash and more
- **Venue names:** 3,787 of 9,490 venues have a name; 249 are confirmed (tagged on the court) and the rest are inferred from the park, school or club the court sits inside, labelled as such
- **Courts by surface and indoor/outdoor** (`mart_sport_surface_coverage`), and an honest **gaps report** for all 75 sports (`mart_sport_gaps`, snapshot in [`docs/coverage_snapshot.md`](docs/coverage_snapshot.md)): 9 sports well covered, 13 tagged but empty in California, 53 with no OpenStreetMap tag at all
- **31 automated tests** across 15 models (all passing, plus one deliberate warning on the sport count) that catch bad data before anyone sees it
- The same project runs on **local DuckDB and Snowflake** with identical results, including a geospatial search ("padel within 12 miles of downtown")

## How it fits together
![Architecture: sources, Python ingestion, a dbt project on DuckDB or Snowflake, and the planned map app](docs/architecture.svg)

## 60-second demo
```bash
pip install -r requirements.txt
make demo      # extract -> load -> build -> test
```
Then open `courtconnect.duckdb` and query `marts.mart_sport_coverage`.

**The story to tell:** *"Here's the messy spreadsheet; here's the clean table. Here's California: 26,000 anonymous map points became 9,500 places, and naming them took the share with a name from 2% to 40%. But 53 of the 75 sports can't be found in this source at all, so I built the gaps report to show exactly where the data is thin instead of hiding it."*

## The sports list: `all_racquet`
The sheet tab **All Raquet** is the source of truth for which sports the platform supports. It is loaded as the
`raw.all_racquet` table (a dbt seed), then cleaned into `dim_sport`.

```bash
make sync-sports   # re-pull the sheet -> transform/seeds/all_racquet.csv
make build         # reload and re-test
```
**Editing the list.** The Google Sheet is the single place to edit (rename a sport, fix a typo, add a new one). The sheet's owner
account can edit it; "anyone with the link" is view-only, which is what lets the sync read it without a login. To let a second
account edit, the owner shares the sheet with it as *Editor*. Never edit `transform/seeds/all_racquet.csv` or the
Snowflake `RAW.ALL_RACQUET` table by hand: the next sync overwrites both.

Alternate names for a sport (e.g. "Frescobol" for Frescoball) go in [`transform/seeds/sport_aliases.csv`](transform/seeds/sport_aliases.csv).
Sports that OpenStreetMap cannot find, and why, are listed in [`docs/sport_name_review.md`](docs/sport_name_review.md).

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
- [x] Statewide extract and venue naming from enclosing parks / schools / clubs ([ADR 0004](docs/decisions/0004-statewide-extract-and-venue-naming.md))
- [ ] Second source (Google Places + club directories) for the 53 untagged sports, surfaces, indoor and beach courts, and confirmed names
- [ ] S3 landing zone, Snowpipe, Terraform
- [ ] Events and ticketing (pro/amateur matches, watch parties)
- [ ] Synthetic social layer (groups, sessions) with PII masking policies
- [ ] Map app / Streamlit front end
