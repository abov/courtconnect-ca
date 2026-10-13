# CourtConnect California: case study

A free map of racket-sport venues in California (tennis, pickleball, padel, squash, badminton, beach tennis and about 70 more), built end to end as a solo project: ingestion, a tested dbt warehouse, and a static map. Live map and code: https://github.com/abov/courtconnect-ca. Data model and lineage: `/dbt-docs/` on the Pages site.

## The problem
Players of smaller racket sports cannot answer "where can I play this near me, and can I walk on?" Each sport has its own scattered, incomplete sources, and the big map platforms treat a tennis court and a padel court as the same pin. Existing sources also disagree: OpenStreetMap has courts but few names, business directories have names but not courts, and clubs publish access rules only on their own pages.

## Users and constraints
- **Users:** me and friends who play several sports; later, possibly the wider community (open source or paid, not decided).
- **Constraints I set on purpose:** link out only (no bookings or payments); public pages only, never my own logins (ADR 0007); no Google Places data, whose terms forbid storing it (ADR 0005); every model must run unchanged on DuckDB and Snowflake.

## What I built
| Layer | What | Why it matters |
|---|---|---|
| Ingestion | Python extract/load of OpenStreetMap courts and Overture places, plus a link checker | Repeatable raw layer; CI uses a small committed fixture, never a live API |
| Warehouse | dbt (DuckDB for dev and CI, Snowflake for prod), 145 models/seeds/tests, `adapter.dispatch` macros | One codebase, two engines; tests guard the logic (clusters converge, every court has one venue, evidence required) |
| Serving | Static MapLibre page fed by a 2 MB JSON export; GitHub Pages | Zero hosting cost; CI fails if the export is stale |
| Operations | Bi-weekly refresh runbook, scheduled task, contributor workflow (issue form to PR), evidence checker | The data stays current without me guessing what changed |
| Governance | 12 ADRs and a confirmation scale (visited / official / reported / inferred) | Every claim says how we know it |

## Decisions and trade-offs (the interesting part)
1. **Cluster courts into venues by proximity (ADR 0003).** OSM stores individual courts; users want places. Trade-off: some wrong merges and wrong splits, so a convergence test and a human-review mart exist.
2. **Honesty over polish (ADR 0007).** "Members only" is often inferred from a club's website, not stated. The map labels it inferred and the contributor workflow demands evidence and a date. I chose a smaller, trustworthy dataset over a bigger, guessed one.
3. **What I chose not to do (ADRs 0005, 0009, 0010, 0012).** No Google Places, no scraping of Meta, WhatsApp or Meetup, no use of my logins. Social and chat groups are link-outs from a club's own page only. This cut off easy data but removed legal and privacy risk, and it is the reason this could become open source or a product.
4. **Treat "also played" sports as inferred (sport_also_played).** Pickleball courts can host Skyball or Typti; counting them as extra courts would overstate supply. They are shown as also played, grouped under the physical court count, and excluded from name-inferred and members-only places.
5. **Give back to the source (ADR 0011).** OSM is the main input, so the map links venues to the OSM editor with a contributor guide, rather than copying fixes privately.

## How quality is measured and kept
- **Scorecard** (`docs/data_quality.md`, `make quality`): service levels for freshness, dead links and name quality, with a dated trend file. Today 5 of 6 are met; the miss is real: only about 12% of venues have a confirmed name (goal 25%), because most OSM courts are unnamed. That gap is the top backlog item.
- **Tests:** 94 dbt tests plus CI checks for seed evidence and export freshness.
- **Runbook:** a written, repeatable bi-weekly procedure for tournaments, social links and WhatsApp/Meetup links.

## An incident worth learning from
PR #7 changed seeds but never re-exported `venues.json`, so the live site silently missed new sports and 43 events. Fix: re-export (#8) and a CI check that fails when the export is stale (#9). Lesson: a derived artifact needs an automated freshness guard, not a reminder.

## Results
- 9,941 venues, 21 of 75 sports with at least one venue, 43 upcoming events, 92 verified link-outs, 100 hand-curated entries with an evidence trail (numbers from the 2026-10-13 scorecard).
- Usage: *[add after instrumenting: weekly visitors, venue opens, link-out clicks]*.
- Friend feedback: *[add after a feedback round: what they searched for, what was missing]*.

## What I would do next
1. Instrument usage with a privacy-friendly counter and define one north-star metric (link-outs per week).
2. Raise name quality with a contributor drive and the OSM link.
3. Decide the path: community open source (needs moderation and a licence plan: ODbL attribution is already required) or a paid layer (for example club-managed listings); the link-out-only rule keeps both options open.
4. Move the scheduled refresh into CI and add alerts on SLA breaches.

## Skills this shows
Data modelling and testing (dbt, two warehouses), pipeline operations (freshness checks, runbooks), data governance (provenance, licences, privacy), product scoping (what not to build), and documentation of decisions.
