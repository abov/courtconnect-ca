# Architecture

![Architecture diagram](architecture.svg)

The same flow as text:

```
Google Sheet (master sports list) ─┐
OpenStreetMap courts, walls (Overpass) ─┤
OpenStreetMap parks, schools, clubs ────┼─► RAW ─► STAGING ─► INTERMEDIATE ─► CORE ─► MARTS ─► export ─► venues.json ─► map
Overture places + addresses (S3) ───────┤  (landing) (clean)   (graph, joins)  (dims)  (what users read)
Census boundaries ──────────────────────┤
Hand-edited seeds (with evidence) ──────┘
   extract / sync (Python)               load (idempotent)        dbt: tests, docs, lineage
```

No server or API: the static page in `app/` reads one exported file, `app/data/venues.json`, hosted on GitHub Pages.

## Layers (dbt, DuckDB)

| Layer | Objects | Purpose |
|---|---|---|
| raw | OSM courts, walls and parents, Overture places and addresses, Census boundaries, `all_racquet`, tag maps (full list: `transform/models/sources.yml`) | Untouched source data. `all_racquet` is synced from the Google Sheet. |
| seeds | about 28 CSVs in `transform/seeds/`: `manual_venues`, `venue_actions`, `watch_events`, `social_events`, `venue_leads`, `place_sport_overrides`, `closed_places`, `sport_aliases` and others | Human knowledge as code. Every fact carries `evidence` + `verified_on`. |
| staging | `stg_*` (one per source or seed) | Typed, standardised, de-duplicated. Surface and indoor/outdoor derived here. |
| intermediate | `int_court_pairs`, `int_court_clusters`, `int_court_parent`, `int_place_venue_match`, `int_manual_venue_match`, `int_venue_address`, `int_wall_clusters` | Proximity graph, venue clustering, enclosing park / school / club, Overture-to-OSM matching, address tiers and the home-privacy check |
| core | `dim_venue`, `dim_court`, `dim_place`, `dim_sport`, `dim_wall`, `bridge_*`, `ref_sport_fit` | Business entities |
| marts | `mart_venue_finder`, `mart_court_finder`, `mart_venue_confidence`, `mart_sport_evidence`, `mart_venue_actions`, `mart_watch_events`, `mart_social_events`, `mart_wall_pins`, `mart_venue_leads`, `mart_places_to_review`, coverage and quality marts | What the export and reports read |

- `mart_venue_finder`: one row per (venue, sport), with surfaces, indoor/outdoor, address and website.
- `mart_court_finder`: one row per (court, sport), for drawing individual courts on a map.
- `mart_venue_confidence`: the rules-based trust score behind the pin styling (confirmed, business listing, inferred).
- `mart_sport_gaps`: every sport with an honest status (`covered`, `sparse`, `tagged_none_found`, `no_osm_tag`) and the next source to try.

Warehouse: **DuckDB only** (ADR 0018; Snowflake retired 2026-10-14, see ADR 0001 for the original plan). Existing `adapter.dispatch` macros stay; new SQL needs no engine-portable form.

## Lifecycle

1. **Sync** (twice a month, [`monthly_refresh.md`](monthly_refresh.md)): `make sync-sports`, `make extract`, `make load`.
2. **Fill**: Overture address points, reverse-geocode of blanks (cached Nominatim, 1 request a second), OSM parents, city from Census boundaries.
3. **Intake**: `make sync-reports` (approved community-form reports become seed edits) and `make issues` (read-only triage).
4. **Build**: `make build` runs seeds, models and tests.
5. **Export**: `make app-data` writes `venues.json`; it is committed.
6. **Measure**: `make quality` (scorecard with a 35-day freshness SLA), `make report`, `make eval-match`.
7. **Ship**: PR, CI, squash-merge; `pages.yml` deploys by itself when `app/**` changed.

Between syncs, the suggest-a-change flow (ADR 0008) turns an approved issue into a one-row seed PR through `issue-to-pr.yml`. Issue text is untrusted and reaches the script through environment variables only.

## CI/CD (GitHub Actions)

- **`ci.yml`** (every push and PR) never calls live sources. It loads a small real-data sample (`ci/fixtures`, Pasadena area), runs the gate scripts, then `dbt build`. Gates: seed evidence, sport names, export freshness, review-priority file, sync-reports test, gold-set match check, scorecard no-regression against main, and the offline LLM-reader guard rail.
- **`issue-to-pr.yml`**: approved issue to a PR that edits one seed row.
- **`pages.yml`**: builds dbt docs and deploys `app/` to GitHub Pages. Runs on every push to main that touches `app/**` or the workflow (so merging an app or export change publishes it), and by hand (`workflow_dispatch`), e.g. after a change under `transform/` that should reach the dbt docs.
- Never hand-resolve `venues.json` conflicts: take main's copy, rebuild, re-export.

## Data access, storage and privacy

- **In:** public and open sources only (OSM, Overture, Census, public pages, community reports). No Google Places (ADR 0005), no owner logins (ADR 0007), the project User-Agent only on outgoing requests.
- **Stored:** raw CSVs in one shared folder (the main checkout's `data/raw`), the DuckDB file per worktree (`make fresh-db` rebuilds it), seeds and `venues.json` in git.
- **Out:** one static JSON file. Phone numbers are never exported; residential homes show the city only.

## ML and agents

Models and LLMs only suggest; code, tests and people decide. See [`ml_plan.md`](ml_plan.md) (review-queue ranker, address fill, LLM page reader with quote checking, aerial pilot), ADR 0017 (page reader), ADR 0019 and [`self_service_plan.md`](self_service_plan.md) (staged agent autonomy), and [`ml_strategy.md`](ml_strategy.md) (the order and case for AI taking over the project's work).

Decisions: [`docs/decisions`](decisions). Coverage: [`coverage_snapshot.md`](coverage_snapshot.md). Sports we cannot find: [`sport_name_review.md`](sport_name_review.md). All tools and strategies: [`tools_and_strategies.md`](tools_and_strategies.md).
