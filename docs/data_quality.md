# Data quality scorecard

Generated 2026-11-10 by `make quality` (`ingestion/export_quality_scorecard.py`) from the current DuckDB build. Targets are stated service levels, not guarantees: they are set in the script and a breach is reported, not hidden.

## Service levels

| Measure | Now | Target | Status |
|---|---|---|---|
| OSM extract age | 0 days | <= 90 days | OK |
| Oldest current link-out check | 31 days | <= 60 days | OK |
| Oldest upcoming-event check | 12 days | <= 14 days | OK |
| Oldest current social-series check | 20 days | <= 35 days | OK |
| Website link-check age | 13 days | <= 60 days | OK |
| Dead venue websites (of checked) | 0.0 % | <= 10.0 % | OK |
| Venues seen in the last 35 days | 100.0 % | >= 99.0 % | OK |
| Venues with a real name | 18.3 % | >= 25.0 % | **BREACH** |

**7 of 8 service levels met.**

## Coverage

- Venues on the map: **16,919** (15,020 in OpenStreetMap, 1,448 in Overture places, 1,688 hand-curated; sources overlap).
- Of those, hitting-wall venues (ADR 0032; a wall that stands at no listed court venue): **389**; court venues: **16,530**.
- Venues with a real name: **3,103** (18.3%). The rest carry a name guessed from the park or school, or none.
- Venues with a usable website: **2,265** (13.4%).
- Sports on the sheet: **82**; with at least one venue: **43**; empty: **39**.

## Trust labels (hand-curated venues)

| Confirmation | Venues |
|---|---|
| official | 1723 |
| reported | 309 |
| visited | 3 |

Visited = seen in person; official = stated on the operator's own page; reported = told to us, not verified. Inferred data is labeled inferred on the map and never counted as confirmed.

Community reports: **0** venues reported by 1 person, **0** by 2 or more (2+ independent reports let a reviewer consider raising the level; nothing is raised automatically).

## Confidence bands (all venues, inferred)

Rule-based score from `mart_venue_confidence` (rules_v2): high >= 60, medium 30-59, low < 30. It is an inferred heuristic for prioritizing review, not a probability; it is not shown on the map.

| Band | All | AZ | CA | HI | MX | NV | OR | WA |
|---|---|---|---|---|---|---|---|---|
| high | 1,468 | 111 | 614 | 40 | 276 | 98 | 128 | 201 |
| medium | 1,127 | 68 | 659 | 40 | 197 | 39 | 41 | 83 |
| low | 14,355 | 1,911 | 8,811 | 372 | 57 | 410 | 1,002 | 1,792 |
| total | 16,950 | 2,090 | 10,084 | 452 | 530 | 547 | 1,171 | 2,076 |

## Freshness

- OSM extract: 0 days old.
- Current link-outs: 662; 0 older than 60 days.
- Upcoming events: 76; 0 not re-checked in 14+ days.
- Current social series: 37; 0 not re-checked in 35+ days.
- Website liveness check: 13 days old; 0 of 949 checked venue sites dead (0.0%).
- Venues seen by any source in the last 35 days: 16,946 of 16,950 (100.0%); oldest date 2026-10-10; 4 undated. Sources: OSM extract date, Overture release date, hand-added confirmation, link-out check (monthly runbook: docs/monthly_refresh.md).

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
| new | 177 |
| resolved | 98 |
| needs_location | 19 |
| confirmed | 11 |
| rejected | 10 |
| needs_visit | 5 |

## Tests

Last dbt run: 308 tests passed, 0 warned, 0 failed.

History: [data_quality_trend.csv](data_quality_trend.csv) (one row per run).
