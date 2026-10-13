# 0012. Meetup and Partiful sources (link-out only), Eventful dropped

Date: 2026-10-13. Status: accepted (2026-10-13). Extends ADRs 0009 and 0010.

## Context
Local open play, socials and clinics are often run as Meetup groups or Partiful events. We want to point people at them under the same rules as other social sources.

## Decision
- **Meetup:** public group and event pages may be linked out. Its API is gated (paid), so there is no scraping and no owner login (ADR 0007).
- **Partiful:** invite-style pages with no public API, and many events are private. Link only public `partiful.com/e/...` pages that a club's own site shows or a contributor submits through suggest-a-change. Never search behind a login.
- **Eventful:** dropped. The service is believed to have shut down around 2020-21, so there is nothing to link to. (Owner decision, 2026-10-13.)
- How: `venue_actions.csv` rows with `action_type=social`, `provider=meetup|partiful`, plus `verified_on` and `evidence` saying where the link was seen. Label reported unless the club's own site shows it (then official). Never copy descriptions, attendee lists or member names.

## Build
- `ci/check_seed_evidence.py` accepts `meetup.com` and `partiful.com/e` URLs for social rows; the map labels the providers "Meetup" and "Partiful".
- No rows are added now: none have been seen on a club's own site yet.

## Freshness
Events end and links die. Recheck in the bi-weekly runbook (`docs/tournament_refresh.md`); remove dead ones.

## Consequences
Honest and compliant, but shows no live listing and misses groups that clubs do not link from their own sites.
