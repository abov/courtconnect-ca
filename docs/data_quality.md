# Data quality scorecard

Generated 2026-10-14 by `make quality` (`ingestion/export_quality_scorecard.py`) from the current DuckDB build. Targets are stated service levels, not guarantees: they are set in the script and a breach is reported, not hidden.

## Service levels

| Measure | Now | Target | Status |
|---|---|---|---|
| OSM extract age | 5 days | <= 90 days | OK |
| Oldest current link-out check | 4 days | <= 60 days | OK |
| Oldest upcoming-event check | 5 days | <= 14 days | OK |
| Website link-check age | 4 days | <= 60 days | OK |
| Dead venue websites (of checked) | 0.0 % | <= 10.0 % | OK |
| Venues seen in the last 35 days | 99.9 % | >= 99.0 % | OK |
| Venues with a real name | 11.6 % | >= 25.0 % | **BREACH** |

**6 of 7 service levels met.**

## Coverage

- Venues on the map: **9,941** (9,490 in OpenStreetMap, 1,013 in Overture places, 93 hand-curated; sources overlap).
- Venues with a real name: **1,152** (11.6%). The rest carry a name guessed from the park or school, or none.
- Venues with a usable website: **707** (7.1%).
- Sports on the sheet: **75**; with at least one venue: **21**; empty: **54**.

## Trust labels (hand-curated venues)

| Confirmation | Venues |
|---|---|
| official | 86 |
| reported | 25 |
| visited | 3 |

Visited = seen in person; official = stated on the operator's own page; reported = told to us, not verified. Inferred data is labeled inferred on the map and never counted as confirmed.

## Freshness

- OSM extract: 5 days old.
- Current link-outs: 92; 0 older than 60 days.
- Upcoming events: 43; 0 not re-checked in 14+ days.
- Website liveness check: 4 days old; 0 of 125 checked venue sites dead (0.0%).
- Venues seen by any source in the last 35 days: 9,932 of 9,941 (99.9%); oldest date 2026-09-23; 9 undated. Sources: OSM extract date, Overture release date, hand-added confirmation, link-out check (monthly runbook: docs/monthly_refresh.md).

Stale or undated venues (first 9):

| Venue | Source | Last seen |
|---|---|---|
| Alondra Park | manual | undated |
| Calabasas Pickleball Club | manual | undated |
| Charles H. Wilson Park | manual | undated |
| Elenda Paddle Tennis Courts | manual | undated |
| Jim Gilliam Park Tennis Court | manual | undated |
| Ladera Linda Community Park | manual | undated |
| Manhattan Beach Heights | manual | undated |
| Oberrieder Park Paddle Tennis Courts | manual | undated |
| Shorecliff Golf Club | manual | undated |

## Open leads

| Status | Leads |
|---|---|
| new | 74 |
| resolved | 6 |
| needs_location | 2 |
| confirmed | 1 |
| needs_visit | 1 |

## Tests

Last dbt run: 108 tests passed, 0 warned, 0 failed.

History: [data_quality_trend.csv](data_quality_trend.csv) (one row per run).
