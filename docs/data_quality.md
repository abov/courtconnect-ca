# Data quality scorecard

Generated 2026-10-24 by `make quality` (`ingestion/export_quality_scorecard.py`) from the current DuckDB build. Targets are stated service levels, not guarantees: they are set in the script and a breach is reported, not hidden.

## Service levels

| Measure | Now | Target | Status |
|---|---|---|---|
| OSM extract age | 1 days | <= 90 days | OK |
| Oldest current link-out check | 14 days | <= 60 days | OK |
| Oldest upcoming-event check | 12 days | <= 14 days | OK |
| Oldest current social-series check | 3 days | <= 35 days | OK |
| Website link-check age | -1 days | <= 60 days | OK |
| Dead venue websites (of checked) | 0.0 % | <= 10.0 % | OK |
| Venues seen in the last 35 days | 100.0 % | >= 99.0 % | OK |
| Venues with a real name | 16.1 % | >= 25.0 % | **BREACH** |

**7 of 8 service levels met.**

## Coverage

- Venues on the map: **10,277** (9,653 in OpenStreetMap, 995 in Overture places, 725 hand-curated; sources overlap).
- Venues with a real name: **1,652** (16.1%). The rest carry a name guessed from the park or school, or none.
- Venues with a usable website: **1,196** (11.6%).
- Sports on the sheet: **81**; with at least one venue: **39**; empty: **42**.

## Trust labels (hand-curated venues)

| Confirmation | Venues |
|---|---|
| official | 795 |
| reported | 83 |
| visited | 3 |

Visited = seen in person; official = stated on the operator's own page; reported = told to us, not verified. Inferred data is labeled inferred on the map and never counted as confirmed.

Community reports: **0** venues reported by 1 person, **0** by 2 or more (2+ independent reports let a reviewer consider raising the level; nothing is raised automatically).

## Confidence bands (all venues, inferred)

Rule-based score from `mart_venue_confidence` (rules_v2): high >= 60, medium 30-59, low < 30. It is an inferred heuristic for prioritizing review, not a probability; it is not shown on the map.

| Band | All | CA | NV |
|---|---|---|---|
| high | 696 | 598 | 98 |
| medium | 696 | 659 | 37 |
| low | 8,896 | 8,486 | 410 |
| total | 10,288 | 9,743 | 545 |

## Freshness

- OSM extract: 1 days old.
- Current link-outs: 285; 0 older than 60 days.
- Upcoming events: 85; 0 not re-checked in 14+ days.
- Current social series: 21; 0 not re-checked in 35+ days.
- Website liveness check: -1 days old; 0 of 882 checked venue sites dead (0.0%).
- Venues seen by any source in the last 35 days: 10,284 of 10,288 (100.0%); oldest date 2026-09-23; 4 undated. Sources: OSM extract date, Overture release date, hand-added confirmation, link-out check (monthly runbook: docs/monthly_refresh.md).

Stale or undated venues (first 4):

| Venue | Source | Last seen |
|---|---|---|
| Beach Tennis San Diego courts (Brighton Ave, Ocean Beach) | manual | undated |
| Calabasas Pickleball Club | manual | undated |
| Manhattan Heights Park | manual | undated |
| PDR | manual | undated |

## Open leads

| Status | Leads |
|---|---|
| new | 82 |
| resolved | 74 |
| rejected | 9 |
| needs_location | 7 |
| needs_visit | 1 |
| confirmed | 1 |

## Tests

Last dbt run: 231 tests passed, 0 warned, 0 failed.

History: [data_quality_trend.csv](data_quality_trend.csv) (one row per run).
