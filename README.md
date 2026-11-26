# RacketConnect

**Find where to play, who to play with, and where to watch, for every racket sport in California, Nevada, Oregon, Washington, Idaho, Utah, Arizona, New Mexico, Texas, Hawaii and parts of Mexico** (scope: [ADR 0014](docs/decisions/0014-ca-nv-scope.md), growing in [ADR 0028](docs/decisions/0028-five-state-scope.md)).

**[Open the live map](https://abov.github.io/courtconnect-ca/)** · [Project hub](https://abov.github.io/courtconnect-ca/hub.html) (every doc, page and tool starts there)

| Play | Watch |
|---|---|
| ![Pickleball venues across LA and Orange County, clustered, with filters](docs/screenshots/map-play.png) | ![Upcoming pro events across California, with dates and organizer links](docs/screenshots/map-watch.png) |

One free map of every racket sport, from park courts and hitting walls to private clubs. Each fact is labelled official, reported or inferred, with dates ([ADR 0007](docs/decisions/0007-confirmation-levels-and-leads.md)). It links out to the venue's or organizer's own site and takes no bookings or payments. How it differs from other apps: [competitor scan](docs/competitor_scan.md).

Builders and AI tools: [`app/data/venues.json`](app/data/venues.json), the [data dictionary](app/data-dictionary.md) and [`llms.txt`](app/llms.txt).

**Stack:** Python ingestion, a tested dbt project on DuckDB, a static MapLibre page on GitHub Pages. No server, accounts or cookies. Map data from OpenStreetMap and Overture Maps ([`NOTICE.md`](NOTICE.md)); Google Places is not used ([ADR 0005](docs/decisions/0005-overture-places-and-google-terms.md)) and only public pages are read ([ADR 0007](docs/decisions/0007-confirmation-levels-and-leads.md)). Architecture: [`docs/architecture.md`](docs/architecture.md).

## Run it
```bash
pip install -r requirements.txt
make fresh-db   # rebuild the database from the shared raw data (~1 min)
make demo       # or extract, load, build and test from public sources (extract ~15 min)
make app-data   # export the map data
make app        # open http://localhost:8765
```
`make build` (dbt seeds, models and tests) is the main check after any change to `transform/`. Every `make` target: [`docs/commands.md`](docs/commands.md). Routes without a full extract, the sample-data build and the Windows helpers are in [`docs/data_guide.md`](docs/data_guide.md). The raw data is not stored in this repo, and the `.duckdb` file is never committed.

## Edit the data
Data lives in seeds under `transform/seeds/`: edit them, then `make build` and `make app-data`. Which seed does what, and how the sports list is synced from its sheet: [data guide](docs/data_guide.md).

## Contribute and maintain
- Something wrong or missing: "Fix or add your listing" on the map's About card, or [how to contribute](CONTRIBUTING.md).
- Twice-monthly refresh: [`docs/monthly_refresh.md`](docs/monthly_refresh.md). Current priorities: [`docs/status.md`](docs/status.md).
- Decisions: one short record each in [`docs/decisions/`](docs/decisions).
- Reusing it for another area or sport: the covered region is one file, `ingestion/regions.json`; see the [fork guide](docs/fork_guide.md).
