# Data quality scorecard

Generated 2026-10-13 by `make quality` (`ingestion/export_quality_scorecard.py`) from the current DuckDB build. Targets are stated service levels, not guarantees: they are set in the script and a breach is reported, not hidden.

## Service levels

| Measure | Now | Target | Status |
|---|---|---|---|
| OSM extract age | 4 days | <= 90 days | OK |
| Oldest current link-out check | 3 days | <= 60 days | OK |
| Oldest upcoming-event check | 4 days | <= 14 days | OK |
| Website link-check age | 3 days | <= 60 days | OK |
| Dead venue websites (of checked) | 0.0 % | <= 10.0 % | OK |
| Venues with a real name | 11.6 % | >= 25.0 % | **BREACH** |

**5 of 6 service levels met.**

## Coverage

- Venues on the map: **9,941** (9,490 in OpenStreetMap, 1,013 in Overture places, 79 hand-curated; sources overlap).
- Venues with a real name: **1,152** (11.6%). The rest carry a name guessed from the park or school, or none.
- Venues with a usable website: **707** (7.1%).
- Sports on the sheet: **75**; with at least one venue: **21**; empty: **54**.

## Trust labels (hand-curated venues)

| Confirmation | Venues |
|---|---|
| official | 72 |
| reported | 25 |
| visited | 3 |

Visited = seen in person; official = stated on the operator's own page; reported = told to us, not verified. Inferred data is labeled inferred on the map and never counted as confirmed.

## Freshness

- OSM extract: 4 days old.
- Current link-outs: 92; 0 older than 60 days.
- Upcoming events: 43; 0 not re-checked in 14+ days.
- Website liveness check: 3 days old; 0 of 111 checked venue sites dead (0.0%).

## Open leads

| Status | Leads |
|---|---|
| new | 55 |
| resolved | 6 |
| needs_location | 2 |
| needs_visit | 1 |
| confirmed | 1 |

## Tests

Last dbt run: 94 tests passed, 0 warned, 0 failed.

History: [data_quality_trend.csv](data_quality_trend.csv) (one row per run).
