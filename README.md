# CourtConnect CalNeva

**Find where to play, who to play with, and where to watch, for every racket sport in California and Nevada** ("CalNeva", [ADR 0014](docs/decisions/0014-calneva-scope.md)).

**[Open the live map](https://abov.github.io/courtconnect-ca/)**

| Find a place to play | Watch a match |
|---|---|
| ![Pickleball venues across LA and Orange County, clustered, with filters](docs/screenshots/map-play.png) | ![Upcoming pro events across California, with dates and organizer links](docs/screenshots/map-watch.png) |

*CourtConnect is a discovery tool for all racket sports: it finds where to play or watch, then sends you to the venue's or organizer's own site. It sells no tickets and takes no bookings or payments.*

Tennis, padel, pickleball and squash and dozens of lesser-known and up-and-coming racket sports are booming, but information about *where to play* is scattered and messy. This project collects it, cleans it, checks it, and says honestly how complete it is.

## What it does
- **Venue map** from two open sources (OpenStreetMap and Overture Maps), with courts grouped into venues by proximity. Filter by sport, surface, indoor/outdoor, access, or search by name or city. Filters live in the URL, so any view is shareable.
- **Honest about confidence:** pins show how much to trust each name and sport (confirmed, business listing, inferred). A **How complete is this data?** panel lists every sport, including those with no data yet.
- **Link-outs** to a venue's own pages for open play, lessons and leagues, each with a `verified_on` date and an evidence note. **Watch a match** mode and a hitting-wall map.
- **Quality checks:** dbt tests, a coverage report and a `make quality` scorecard catch bad data and stale entries.

Mission: One map for every racket sport in California and Nevada: find a court, watch a match, try a new racket sport, and eventually find people to play with. Live counts: [`docs/coverage_snapshot.md`](docs/coverage_snapshot.md).

## What the data showed
Numbers are dated and come from the notes linked in each row.

| Finding | What it means |
|---|---|
| **No single source is enough.** 25,971 OSM court records became 9,941 venues; only 4,362 had a name, and Overture added 435 venues OSM had no court for ([snapshot, 10-14](docs/coverage_snapshot.md)). | OSM knows where courts are, business listings know names. Joining them is the product. |
| **The map is mostly tennis.** Of the 76 sports on the master sheet, 19 are covered and 45 have nothing found ([snapshot](docs/coverage_snapshot.md)). | Gaps are the story for lesser-known sports, so the app shows them instead of hiding them. |
| **Duplicates were inflating the count.** Merging courts inside one park or school, and places at one street address, cut venues from 10,542 to 10,235 (-3%). A guard test now fails if two venues share a name within 150 m. | Fix the cause, then add a test so it cannot return. |
| **About 90% of venues have no street address** ([ML plan](docs/ml_plan.md)). | Most are park and school courts. Plan: nearest-address lookup, labelled inferred. |
| **Pickleball hides on tennis courts.** Painted lines are rarely tagged, so a re-extract cannot find them; city park pages and owner reports did ([ML plan](docs/ml_plan.md)). | Refreshing data does not fix a data gap; a different source does. |
| **Gyms and public facilities hold niche sports.** Chain and city pages added racquetball (105 venues: CA 90, NV 15) plus YMCA pickleball ([gym scan](docs/gym_chain_scan.md)). | Chain-by-chain scans beat generic search for sports like racquetball. |
| **Websites go bad.** One club domain was hijacked and another belonged to a club in a different state. | Links are checked and flagged (`make check-websites`), not trusted. |

## ML strategy: small models suggest, people decide
Rule: **a model may rank or suggest; it never writes to the map.** Anything inferred is labelled as such. Full plan: [`docs/ml_plan.md`](docs/ml_plan.md).

| Phase | What | Result so far |
|---|---|---|
| 1. Review-queue ranker (built) | Logistic regression on 90 human confirm/reject labels orders about 200 uncertain sport matches, so review time goes to the clearest cases first. | Leave-one-out accuracy 86%, AUC 0.93. |
| 2. LLM reads public pages (planned) | Extracts sport, court count and access from a venue's own page; every field needs an exact quote that code checks is on the page. | Precision to be measured against the hand-checked labels. |
| 3. Courts in aerial photos (pilot) | Object detector on free NAIP imagery, trained on OSM court shapes. | Hawthorne: found 8 of 9 mapped tennis courts and 2 new sites; sport and access cannot be seen. |

Lessons worth keeping:
- **Label skew bites.** Every early Tennis label was a reject, so the ranker learned "Tennis means reject". Confirming real tennis clubs fixed it (Tennis likely-rejects 25 to 4). Check what a model learned, not just its score.
- **No leaks.** The confidence score is not a feature, because human overrides already feed it.
- **Honest limits.** The aerial pilot finds single digits of new sites per city, not hundreds, so it is a lead generator for OSM, not a data source.

## How it fits together
![Architecture: sources, Python ingestion, a dbt project on DuckDB, and the static map app](docs/architecture.svg)

Python ingestion -> dbt (DuckDB) -> static MapLibre page in [`app/`](app) reading one exported file, `app/data/venues.json`. Phone numbers are never exported. Layout: [`docs/architecture.md`](docs/architecture.md). The problem, choices and trade-offs in longer form: [`docs/case_study.md`](docs/case_study.md).

**Skills shown:** SQL and dbt modelling with tests, entity resolution across messy sources, data-quality scorecards and freshness SLAs, small ML with leave-one-out validation, written decision records ([ADRs](docs/decisions)), and scoping work by cost and risk (privacy, terms of use, honesty).

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

Details: [`docs/data_guide.md`](docs/data_guide.md). Twice-monthly refresh routine: [`docs/monthly_refresh.md`](docs/monthly_refresh.md).

## Principles
- **Honesty over polish:** inferred data is labelled as inferred.
- **Link out, never transact.**
- **Open data only:** Overture + OSM; Google Places is not used because its terms forbid storing it ([ADR 0005](docs/decisions/0005-overture-places-and-google-terms.md)).
- **Public pages only:** no use of anyone's logged-in accounts ([ADR 0007](docs/decisions/0007-confirmation-levels-and-leads.md)).
- Models run on **DuckDB** (Snowflake support retired 2026-10-14). Data licenses: [`NOTICE.md`](NOTICE.md).

## Roadmap
- [x] Venue clustering, statewide extract, Overture second source, watch events, link-outs, suggest-a-change flow, Nevada, duplicate guard
- [ ] Beta feedback round, then visual polish ([`docs/ux_polish.md`](docs/ux_polish.md))
- [ ] Sport discovery ("Try something new") and tennis kept visible next to pickleball
- [ ] Social phase A: "Find people to play with" from existing groups; own accounts only after a separate decision
- [ ] More Nevada link-outs, review queue, ML phases 2-3
- [ ] Rename repo and Pages URL to `courtconnect` after the beta
