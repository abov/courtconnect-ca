# 0016. A coach with no court address is rejected, not confirmed

Date: 2026-10-17. Status: accepted (2026-10-17).

## Context
About a third of the places in the sport review queue (`docs/review_priority.csv`) are coaches, lesson businesses and academies (Overture categories such as `fitness_trainer`, `sports_and_recreation`, `gym`). Their websites sell lessons, clinics and camps and often name no court, address or facility. Batches 9-11 rejected these one at a time; batch 11 spent most of its reads on them.

## Decision
- **Rule:** a place whose own public page shows a coach, lesson, clinic or academy business and names **no court address or facility** is rejected for that sport (`place_sport_overrides.csv`, verdict `reject`). It is a service, not a place to play, so it does not get a pin.
- **Not covered (keep reading):** a page that names the venue where it teaches (a park, school, club or street address) is confirmed against that venue; if the venue is already a pin the coach is a lead for it, not a new pin. Academies that run their own facility (address + courts on the page) are confirmed as usual.
- **Evidence still required:** the override row names the page and what it lacks ("lessons and clinics only; no courts or address on the page"), with `verified_on`. One page read per row stays the minimum: do not reject from the Overture row alone.
- **Reversible:** if a later page or community report names the court, a `confirm` row replaces the reject.

## Consequences
Fewer false pins from coaches' home or office addresses (also protects privacy for home-based coaches). Review batches get faster: coach rows are rejected after one page read. A lesson business that genuinely owns courts but hides the address on a Contact page can be missed until someone reports it.
