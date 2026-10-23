# CourtConnect CalNeva

**Find where to play, who to play with, and where to watch, for every racket sport in California and Nevada** ("CalNeva", [ADR 0014](docs/decisions/0014-calneva-scope.md)).

**[Open the live map](https://abov.github.io/courtconnect-ca/)**

| Find a place to play | Watch a match |
|---|---|
| ![Pickleball venues across LA and Orange County, clustered, with filters](docs/screenshots/map-play.png) | ![Upcoming pro events across California, with dates and organizer links](docs/screenshots/map-watch.png) |

*CourtConnect is a discovery tool: it finds where to play or watch, then sends you to the venue's or organizer's own site. It sells no tickets and takes no bookings or payments.*

Pickleball, padel, tennis, squash and dozens of lesser-known racket sports are booming, but information about *where to play* is scattered and messy. This project collects it, cleans it, checks it, and says honestly how complete it is.

## Mission
Help people in California and Nevada **find every place to play or watch racket sports, try something new, and meet others to play with**. Pickleball, tennis, padel, squash and many more all get a home here ([ADR 0015](docs/decisions/0015-mission-and-social-phase.md)).
- **Every sport, side by side:** pickleball and tennis are usually easy to find, and here padel, squash, badminton, table tennis, racquetball, Pop Tennis, paddleball, Basque pelota and more are just as easy to find, so there's always something new to try.
- **Play together:** after "where can I play?" comes "who can I play with?". The next phase links to groups that already exist (open play, clinics, ladders, Meetup/WhatsApp groups); any accounts or matching of our own would come later, and only with its own decision record.

## What it does
- **Venue map** for California and Nevada from two open sources (OpenStreetMap and Overture Maps), with courts grouped into venues by proximity. Filter by sport, surface, indoor/outdoor, access, or search by name or city. Filters live in the URL, so any view is shareable.
- **Honest about confidence:** pins show how much to trust each name and sport (confirmed, business listing, inferred), and a **How complete is this data?** panel lists every sport with its status, including those with no data yet.
- **Link-outs** to a venue's own pages for open play, lessons, leagues and tournaments, each with a `verified_on` date and an evidence note.
- **Watch a match** mode for upcoming events with the organizer's link, and a map of hitting walls.
- **Quality checks:** dbt tests, a coverage report and a `make quality` scorecard catch bad data and stale entries.

Live numbers (venues, sports, link-outs) are in [`docs/coverage_snapshot.md`](docs/coverage_snapshot.md), not repeated here.

## How it fits together
![Architecture: sources, Python ingestion, a dbt project on DuckDB, and the static map app](docs/architecture.svg)

Python ingestion -> dbt (DuckDB) -> static MapLibre page in [`app/`](app) reading one exported file, `app/data/venues.json`. Phone numbers are never exported. Layout: [`docs/architecture.md`](docs/architecture.md).

## Quick start
```bash
pip install -r requirements.txt
make demo       # extract -> load -> build -> test (extract takes ~15 min)
make app-data   # export the map data
make app        # open http://localhost:8765
```
`make build` runs the dbt seeds, models and tests; it is the main check after any change to `transform/`. On Windows, `view_db.bat` opens `courtconnect.duckdb` read-only in the DuckDB UI (close it before running dbt).

## Editing the data
Data lives in seeds under `transform/seeds/`; edit them, then `make build` and `make app-data`.

| To change | Edit |
|---|---|
| The list of sports | The Google Sheet, then `make sync-sports` (never hand-edit `all_racquet.csv`) |
| Add a venue no dataset knows | `manual_venues.csv` |
| Add a link-out (open play, lessons, ...) | `venue_actions.csv` |
| Add an event to watch | `watch_events.csv` |
| Confirm or reject an uncertain match | `place_sport_overrides.csv` |

Details, column meanings and rules: [`docs/data_guide.md`](docs/data_guide.md). The twice-monthly refresh routine: [`docs/monthly_refresh.md`](docs/monthly_refresh.md).

## Principles
- **Honesty over polish:** inferred data is labelled as inferred, never presented as confirmed.
- **Link out, never transact:** no bookings, tickets or payments.
- **Open data only:** Overture + OSM; Google Places is not used because its terms forbid storing it ([ADR 0005](docs/decisions/0005-overture-places-and-google-terms.md)).
- **Public pages only:** no use of anyone's logged-in accounts ([ADR 0007](docs/decisions/0007-confirmation-levels-and-leads.md)).
- Models run on **DuckDB** (dev, CI and the only warehouse); Snowflake support was retired on 2026-10-14. Decisions are in [`docs/decisions`](docs/decisions). Data licenses: [`NOTICE.md`](NOTICE.md).

## Roadmap
- [x] Venue clustering, statewide extract, Overture second source, watch events, link-outs, suggest-a-change flow, Nevada
- [ ] More Nevada link-outs and venues
- [ ] Beta feedback round, then visual polish ([`docs/ux_polish.md`](docs/ux_polish.md))
- [ ] Sport discovery: "Try something new" cards, lesser-known sports given room, tennis kept visible next to pickleball
- [ ] Social phase A: "Find people to play with" from existing groups (open play, clinics, ladders, Meetup/WhatsApp); own accounts only after a separate decision
- [ ] Clear the human review queue for uncertain sport matches
- [ ] Governing-body and club directories for sports neither source finds
- [ ] Rename repo and Pages URL to `courtconnect` after the beta
