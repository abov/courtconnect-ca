# Plan: finding venues in the rest of the US with the page reader

Written 2026-11-04. PLAN ONLY: nothing here runs, spends money or edits a seed until the owner says so. It scopes track 1 and track 7 of `docs/ml_strategy.md` to one question: how do we find venues in states that have no data layer yet, with the least human reading.

## What the evidence says
- Aerial detection is parked (`docs/articles/the-ml-pilot-i-killed.md`): ~2 new sites per city, pickleball invisible. Not the route.
- Overture and OSM give the net-court skeleton for any state (`docs/new_region_checklist.md`, section 1). The cost per state is section 2, the hand research: city parks and rec, clubs, YMCAs, campuses, walls, events, groups.
- That research is reading public pages. The reader (`ingestion/page_reader.py`, `--engine claude`, quote check, spend cap) already does the reading part. 49 pages have been read so far (`docs/reader_pilot_results.csv`).
- **The gap is finding pages, not reading them.** In the current build only 921 of 9,720 CA venues and 129 of 547 NV venues carry a website (measured 2026-11-04 from `marts.mart_venue_finder`, about 9% and 24%). The reader's pilot input (hand-settled `manual_venues.csv` rows) does not exist for a new state.

## Pilot (one state, chosen by the owner)
1. **URL source, free and public.** Start from each Census place in the state (`data/raw/census_boundaries.csv` already holds places). For the city's official site use Wikidata's "official website" property for the place (public, no key, untested here: measure how many places have one before relying on it). From that site fetch only the parks and recreation pages one hop away (robots.txt respected, project User-Agent, one request per host every few seconds, as the reader already does). Add the state sections of the national bodies (USTA, USA Pickleball, USA Padel and the others in `docs/event_group_search.md`) as a second list.
2. **Read.** `page_reader.py --input urls.csv --engine claude`, dry run first to print pages and the token estimate. Facts stay `inferred` in `docs/reader_candidates.csv`; nothing reaches seeds. A person promotes a candidate into `manual_venues.csv` / `venue_actions.csv` with its evidence, as for every other source.
3. **Order the work with the gap mart.** Rank places by `mart_market_gaps`-style gaps, adding Census population (no key) so a big city with no listed courts is read before a hamlet. Rule-based sort first; a model only if the sort measurably misses.
4. **Measure before scaling.** Hold out 30 pages nobody tuned on. Report per field (sport, courts, setting, access, address, booking link) precision, recall and no-quote share for rules vs the Claude engine, with intervals (`docs/ml_strategy.md`, section 6). Stop rule, written now: if fewer than 10 candidates per 100 pages read survive review as new venues or new link-outs, do not scale; fall back to hand search for that state.

## Cost and limits
- Cheapest first: the free rules engine on every page, the Claude engine only on pages the rules read as sport-relevant but incomplete. Weekly cap per ADR 0019 and the $20 a month ceiling; the dry run gives the real estimate, so quote no price until it has run.
- Pages that block bots stay hand review. Home-like pins never get an inferred street. Operator is not venue.
- Honest label: reader output is "inferred, read from the page", never "confirmed" (ADR 0007, 0017).

## Decisions needed from the owner
1. Which state is the pilot (it should already be queued for CA parity under ADR 0028).
2. OK to spend up to a stated cap on the Claude engine for the held-out comparison.
3. OK to fetch city sites one hop deep (new behaviour for the reader; today it reads listed URLs only).

## Not in this plan
Learned entity matching, aerial imagery, recommender, partnership data (all parked or off limits per `docs/ml_strategy.md` and CLAUDE.md).
