# Data quality scorecard

Generated 2026-10-18 by `make quality` (`ingestion/export_quality_scorecard.py`) from the current DuckDB build. Targets are stated service levels, not guarantees: they are set in the script and a breach is reported, not hidden.

## Service levels

| Measure | Now | Target | Status |
|---|---|---|---|
| OSM extract age | 4 days | <= 90 days | OK |
| Oldest current link-out check | 8 days | <= 60 days | OK |
| Oldest upcoming-event check | 9 days | <= 14 days | OK |
| Website link-check age | 8 days | <= 60 days | OK |
| Dead venue websites (of checked) | 0.0 % | <= 10.0 % | OK |
| Venues seen in the last 35 days | 99.9 % | >= 99.0 % | OK |
| Venues with a real name | 14.0 % | >= 25.0 % | **BREACH** |

**6 of 7 service levels met.**

## Coverage

- Venues on the map: **10,248** (9,653 in OpenStreetMap, 1,007 in Overture places, 428 hand-curated; sources overlap).
- Venues with a real name: **1,438** (14.0%). The rest carry a name guessed from the park or school, or none.
- Venues with a usable website: **977** (9.5%).
- Sports on the sheet: **76**; with at least one venue: **22**; empty: **54**.

## Trust labels (hand-curated venues)

| Confirmation | Venues |
|---|---|
| official | 466 |
| reported | 39 |
| visited | 3 |

Visited = seen in person; official = stated on the operator's own page; reported = told to us, not verified. Inferred data is labeled inferred on the map and never counted as confirmed.

Community reports: **0** venues reported by 1 person, **0** by 2 or more (2+ independent reports let a reviewer consider raising the level; nothing is raised automatically).

## Confidence bands (all venues, inferred)

Rule-based score from `mart_venue_confidence` (rules_v2): high >= 60, medium 30-59, low < 30. It is an inferred heuristic for prioritizing review, not a probability; it is not shown on the map.

| Band | All | CA | NV |
|---|---|---|---|
| high | 400 | 304 | 96 |
| medium | 763 | 724 | 39 |
| low | 9,094 | 8,682 | 412 |
| total | 10,257 | 9,710 | 547 |

## Freshness

- OSM extract: 4 days old.
- Current link-outs: 213; 0 older than 60 days.
- Upcoming events: 54; 0 not re-checked in 14+ days.
- Website liveness check: 8 days old; 0 of 156 checked venue sites dead (0.0%).
- Venues seen by any source in the last 35 days: 10,248 of 10,257 (99.9%); oldest date 2026-09-23; 9 undated. Sources: OSM extract date, Overture release date, hand-added confirmation, link-out check (monthly runbook: docs/monthly_refresh.md).

Stale or undated venues (first 9):

| Venue | Source | Last seen |
|---|---|---|
| Alondra Park | manual | undated |
| Beach Tennis San Diego courts (Brighton Ave, Ocean Beach) | manual | undated |
| Calabasas Pickleball Club | manual | undated |
| Charles H. Wilson Park | manual | undated |
| Elenda Paddle Tennis Courts | manual | undated |
| Ladera Linda Community Park | manual | undated |
| Oberrieder Park Paddle Tennis Courts | manual | undated |
| PDR | manual | undated |
| Shorecliff Golf Club | manual | undated |

## Open leads

| Status | Leads |
|---|---|
| new | 99 |
| resolved | 44 |
| rejected | 6 |
| needs_location | 2 |
| needs_visit | 1 |
| confirmed | 1 |

## Tests

Last dbt run: 172 tests passed, 0 warned, 0 failed.

History: [data_quality_trend.csv](data_quality_trend.csv) (one row per run).
