# Recheck queue (fixed-budget freshness)

Goal: rechecking cost is a number we choose (`--top N` or `--budget-usd`), not something that grows with the venue count. `make rank-rechecks` writes `docs/recheck_queue.csv`; a person or the page reader (ADR 0017, inside the ADR 0019 spend cap) works down it and stops at the cap.

## Score
`expected harm = (views + floor) x p_change`, everything INFERRED (labelled `confirmation = inferred`), no model training.

| Part | Source | Rule |
|---|---|---|
| views | `docs/usage_events.csv`, last 60 days | `venue-view/<venue_id>` counted as is (`traffic_basis` venue); else the venue's city `demand-where` views split over that city's venues (city); else the floor (none) |
| type | `core.dim_venue`, hand-added `access` | commercial 0.25, unknown 0.15, public 0.08 base chance of a visitor-noticeable change in a year (members/club access or a club-like name = commercial; tagged public/free, hitting walls or a park/school-like name = public) |
| source | best hand confirmation, else link-out verification, else the venue source | visited x0.5, official/link-out verified x0.6, reported x0.9, OSM + Overture x1.0, OSM only x1.1, Overture only x1.3 |
| age | newest dated check (`confirmed_on`, `verified_on`) | <=3 months x0.4, <=6 x0.7, <=12 x1.0, <=24 x1.5, older x2.0, never dated x1.4 |
| closure | `mart_venue_closure_signal` (ADR 0026) | +0.35 |
| page | `data/raw/page_checks.csv` (`make check-pages`) | gone +0.40, changed +0.25, error +0.05, unchanged x0.7 |

The constants sit at the top of `ingestion/rank_rechecks.py`. They are starting guesses: after each batch of rechecks, count how many rows really had changed and adjust.

## What traffic exists (2026-11-06)
- Per venue: none. `venue-open` is one total; the map never sends a venue name or id (`app/index.html`, `trackDemand`).
- Per city: `demand-where/<city> <state>` (and `demand-sport-where/<sport> <city>`), sent on each venue open. The state code in the detail is the only geography; there is no country field (Mexico venues would show as a state code).
- Volume is tiny: about 20 `venue-open` events in the 60-day window and 1 `demand-where` row, so today almost every venue ranks by `p_change` alone (`traffic_basis` none). The queue is still a sensible order, but it is not yet traffic-weighted.

## Smallest event to add (proposed, not shipped)
One line next to `track("venue-open")` in `app/index.html`: `trackD("venue-view", v.i);` The map id `v.i` is the public `venue_id` (already put in the "suggest a change" issue link), so it identifies no visitor and no typed text. GoatCounter would get one `event/venue-view/<venue_id>` path per viewed venue (a fixed 32-character id, not a name); `usage_daily.py` already rolls such rows into `usage_events.csv` and `rank_rechecks.py` already reads them. Update the "Never sent" line in `docs/goat_analysis.md` when it ships. Open question for the owner: GoatCounter's free plan may cap the number of distinct paths; check before shipping.

## Cost assumption
`--usd-per-recheck` defaults to 0.05, a guess for one page reread by the reader; replace it with the measured figure from `docs/reader_pilot_results.csv` runs.

## Why there is no auto-expiry of automatic pins (measured 2026-11-06)
Idea: hide an automatic pin (no hand confirmation, no page check) after N months unless a free signal renews it. Measured on the local warehouse (16,506 pins); not built.
- **Presence in the extract renews every pin.** All OSM courts and Overture places are in the latest extracts, the oldest `last_seen_on` is 2026-10-10 and the data only starts 2026-10-09, so N = 6, 12 or 18 months hides 0 pins today (earliest possible expiry 2027-04).
- **Without presence, expiry hides most of the map.** Automatic pins with no Overture place and no live website are 85.6% of CA, 90.5% of AZ, 84.4% of WA, 83.8% of OR, 72.6% of NV, 78.9% of HI and 13.0% of MX (87% of tennis venues, 71% of pickleball). N only sets the date.
- **OSM last-edit age is not an existence signal.** Hawaii test (1,041 elements, `out center tags meta;`): last edited over 6 months ago 87.5%, 12 months 82.6%, 18 months 79.6%, 36 months 68.6%; only 168 edited in 2026. Real courts are rarely re-edited, so edit age would hide working courts. Overture `update_time` covers only the pins with an Overture place (about 11%).
- **Signals that stay viable, each partial:** still in the latest Overture release (and its absence is already the #607 "may be closed" flag), website domain resolves (`website_checks.csv`; 1,277 venues ok, 83 dead; few automatic pins have a site), closure flag absent. Outbound clicks are aggregate only (GoatCounter has no venue id), so they cannot renew a pin.
- **A future expiry would need** a per-venue liveness signal that separates a live OSM-only court from a dead one (none is free today), a first-seen/last-renewed ledger (nothing records pin age), an owner-set default-OFF switch, and it must not become a verified-only gate (ADR 0034, lifted 2026-11-05). Until then the honest tools are the aging label (#604), the Overture-gone flag (#607) and this recheck queue.
