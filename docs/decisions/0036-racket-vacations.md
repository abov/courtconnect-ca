# 0036. Racket sport vacations chip

Date: 2026-11-05. Status: proposed (owner asked for the chip and chose the scope in chat 2026-11-05; build not started). Extends ADR 0015 (one map for every racket sport) and 0028/0034 (resort rule).

## Context
Visitors plan trips around a sport (pickleball resorts in Los Cabos, padel at Riviera Maya resorts, Hawaii tennis ranches). The map shows courts and events but has no trip framing. Resorts' courts can already be venue pins (`docs/hawaii_resorts.md`).

## Decision
1. A third top-level mode ("Racket vacations", `#mode=trips`) with its own seed `racket_vacations.csv`, exported to `app/data/vacations.json`; link-out only, no bookings.
2. **Scope: regions already on the map** (Los Cabos, Riviera Maya, Puerto Vallarta, Hawaii, Palm Springs, Scottsdale and the like). No worldwide destinations; revisit after the December beta.
3. Only rows with `evidence` + `verified_on` show; unverified leads stay in the seed. The case-by-case resort rule applies, with `who_can_play` stating guests-only versus bookable by non-guests.

## Consequences
Plan, columns, leads and build order: `docs/racket_vacations_plan.md`. Four PRs: ADR, seed and models, chip and layer, first verified batch.
