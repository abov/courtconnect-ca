# Data quality scorecard

Generated 2026-11-25 by `make quality` (`ingestion/export_quality_scorecard.py`) from the current DuckDB build. Targets are stated service levels, not guarantees: they are set in the script and a breach is reported, not hidden.

## Service levels

| Measure | Now | Target | Status |
|---|---|---|---|
| OSM extract age | 11 days | <= 90 days | OK |
| Oldest current link-out check | 46 days | <= 60 days | OK |
| Oldest upcoming-event check | 27 days | <= 14 days | **BREACH** |
| Oldest current social-series check | 35 days | <= 35 days | OK |
| Website link-check age | 27 days | <= 60 days | OK |
| Dead venue websites (of checked) | 0.0 % | <= 10.0 % | OK |
| Venues seen in the last 35 days | 98.3 % | >= 99.0 % | **BREACH** |
| Venues with a real name | 28.1 % | >= 20.0 % | OK |

**6 of 8 service levels met.**

## Coverage

- Venues on the map: **24,506** (20,770 in OpenStreetMap, 3,255 in Overture places, 2,565 hand-curated; sources overlap).
- Of those, hitting-wall venues (ADR 0032; a wall that stands at no listed court venue): **393**; court venues: **24,113**.
- Venues with a real name: **6,880** (28.1%). The rest carry a name guessed from the park or school, or none. Counted as real: named by a source or person, or inside a named sports centre, community centre or club/resort.
- Venues with a usable website: **4,448** (18.2%).
- Sports on the sheet: **82**; with at least one venue: **45**; empty: **37**.

## Trust labels (hand-curated venues)

| Confirmation | Venues |
|---|---|
| official | 2450 |
| reported | 546 |
| visited | 3 |

Visited = seen in person; official = stated on the operator's own page; reported = told to us, not verified. Inferred data is labeled inferred on the map and never counted as confirmed.

Community reports: **0** venues reported by 1 person, **0** by 2 or more (2+ independent reports let a reviewer consider raising the level; nothing is raised automatically).

## Confidence bands (all venues, inferred)

Rule-based score from `mart_venue_confidence` (rules_v2): high >= 60, medium 30-59, low < 30. It is an inferred heuristic for prioritizing review, not a probability; it is not shown on the map.

| Band | All | AZ | CA | HI | MX | NM | NV | OR | TX | WA |
|---|---|---|---|---|---|---|---|---|---|---|
| high | 1,938 | 144 | 494 | 50 | 522 | 47 | 63 | 213 | 184 | 221 |
| medium | 2,099 | 65 | 812 | 32 | 468 | 21 | 80 | 36 | 498 | 87 |
| low | 20,498 | 1,897 | 8,788 | 371 | 973 | 467 | 404 | 954 | 4,867 | 1,777 |
| total | 24,535 | 2,106 | 10,094 | 453 | 1,963 | 535 | 547 | 1,203 | 5,549 | 2,085 |

## Freshness

- OSM extract: 11 days old.
- Current link-outs: 1002; 0 older than 60 days.
- Upcoming events: 97; 26 not re-checked in 14+ days.
- Current social series: 157; 0 not re-checked in 35+ days.
- Website liveness check: 27 days old; 0 of 1013 checked venue sites dead (0.0%).
- Venues seen by any source in the last 35 days: 24,126 of 24,535 (98.3%); oldest date 2026-10-10; 4 undated. Sources: OSM extract date, Overture release date, hand-added confirmation, link-out check (monthly runbook: docs/monthly_refresh.md).

Stale or undated venues (first 25):

| Venue | Source | Last seen |
|---|---|---|
| Beach Tennis San Diego courts (Brighton Ave, Ocean Beach) | manual | undated |
| Calabasas Pickleball Club | manual | undated |
| Manhattan Heights Park | manual | undated |
| PDR | manual | undated |
| Calismash | manual | 2026-10-10 |
| Equinox Sports Club/LA | manual | 2026-10-10 |
| Prince O' Whales | manual | 2026-10-10 |
| Padel Up (Culver City) | manual | 2026-10-12 |
| 24 Hour Fitness Costa Mesa Newport Super Sport | manual | 2026-10-14 |
| 24 Hour Fitness Eastvale Super Sport | manual | 2026-10-14 |
| 24 Hour Fitness Fontana Super Sport | manual | 2026-10-14 |
| 24 Hour Fitness Glendale Super Sport | manual | 2026-10-14 |
| 24 Hour Fitness Lancaster West Super Sport | manual | 2026-10-14 |
| 24 Hour Fitness Livermore Super Sport | manual | 2026-10-14 |
| 24 Hour Fitness Orange Village Super Sport | manual | 2026-10-14 |
| 24 Hour Fitness Pleasanton Super Sport | manual | 2026-10-14 |
| 24 Hour Fitness Rancho Cordova Sport | manual | 2026-10-14 |
| 24 Hour Fitness Santee Sport | manual | 2026-10-14 |
| 24 Hour Fitness Stadium Sport | manual | 2026-10-14 |
| 24 Hour Fitness Summerlin Super Sport | manual | 2026-10-14 |
| Bay Club Redondo Beach | manual | 2026-10-14 |
| Betty Ainsworth Sports Center (City of Hawthorne) | manual | 2026-10-14 |
| Chuck Minker Sports Complex | manual | 2026-10-14 |
| Chuck Minker Sports Complex (City of Las Vegas) | manual | 2026-10-14 |
| ClubSport Aliso Viejo | manual | 2026-10-14 |

## Open leads

| Status | Leads |
|---|---|
| new | 373 |
| resolved | 132 |
| needs_location | 23 |
| needs_visit | 12 |
| confirmed | 12 |
| rejected | 10 |

## Tests

Last dbt run: 370 tests passed, 0 warned, 0 failed.

History: [data_quality_trend.csv](data_quality_trend.csv) (one row per run).
