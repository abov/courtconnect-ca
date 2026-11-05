# 0034. Mexico: scope, shape and effort

Date: 2026-11-02. Status: proposed (owner asked on 2026-11-02 to put all of Mexico on the map and to size it; planning only, nothing built; the owner answered language, parity, resorts and timing the same day, see "Owner answers"). Rescoped 2026-11-04: the owner found the full plan (37-46 sessions) too large, so hand-built parity is limited to the border pilot and the six core metros become demand-gated (see "Decision"). Extends ADR 0014 and 0028 (US states); their rules carry over unchanged. Numbered 0034 because Arizona is expected to take 0033.

## Context
ADR 0028 added states one at a time with a "full CA parity" rule and 8-12 small research sessions per big state. Mexico is a country: 32 states, about 130 million people, Spanish-language sources, and thinner OSM/Overture racket-sport data. Run state by state at that cadence it would be roughly 250-380 sessions, so this ADR proposes a different shape. Everything below about pin counts and sessions is an estimate, not measured; a metro trial gives the real ratio before anything else is committed.

## What breaks when the area is a country
1. **`regions.json` shape.** `fips` is a US Census code. Use **one region `MX`** (the country border polygon from OSM, relation id to be verified on Overpass as ADR 0028 did) rather than 32 regions: every two-letter assumption (`load_raw.py` `_??.csv` glob, the `regions` dbt var, `region_code`, `outside_region_bbox`, `accepted_values`, `ci/check_regions.py`) keeps working, and Mexican states become a `subregion` column (ISO 3166-2, e.g. `MX-BCN`) used for city fill and filters. `fips` stays empty for MX. Metros (`--area tijuana`, ...) get `states: ["MX"]`. The country box overlaps CA and AZ at the border; `region_at` already resolves that by polygon (as for Tahoe, OR/WA). Add test points: Tijuana vs San Ysidro, Mexicali vs Calexico, Nogales Sonora vs Nogales AZ, San Luis Rio Colorado vs San Luis AZ, Ciudad Juarez vs El Paso (El Paso is "none"), Cancun, Merida.
2. **Boundaries and places.** `extract_census_boundaries.py` and `place_from_boundaries.py` are Census-only. Proposed: use Overture `divisions` (localities, counties, regions; same S3 access, works worldwide) for municipalities and cities, with INEGI's Marco Geoestadistico as the fallback if coverage is poor. Needs a check in the trial; it is the largest new code in Phase 1.
3. **ZIP search and the ZIP guard.** Mexican codigos postales are 5 digits and collide with covered US ZIPs: Merida is 97000, Oregon is 97xxx. `zipPoint` in `app/index.html` accepts a number within 120 of any ZIP in `zips.json`. v1 adds **no Mexican postal-code search** (a CP stays "not supported yet"; city and colonia search use `places.json`). A CP table needs a licence check of the public catalogue first.
4. **Addresses.** `extract_overture_addresses.py` filters `country = 'US'`. Whether Overture has usable MX address points is unknown (Hawaii had none): the trial answers it, and per-source licences for MX addresses get checked before shipping. Nominatim tiers (`reverse_geocode_blanks.py`) work on OSM anywhere, same 1 request/second, same project User-Agent, same rule that home-like pins never get an inferred street. Mexican addresses are street + number + colonia + CP; the street/city fields need a format check.
5. **Search terms and sports.** `sport_search_terms.csv` (120 rows) and `sport_aliases.csv` are English. Add Spanish terms (padel/pádel, raquetbol, frontenis, fronton, pelota vasca, tenis de mesa, badminton/bádminton, cancha de tenis, club deportivo, unidad deportiva) so Overture name matching sees Mexican places; wrong guesses stay `ambiguous`, as now. Basque pelota/frontenis is already in the sheet; the rule "Basque Pelota only from public online sources" applies.
6. **App.** Default view stays the western mainland; add a "Mexico" shortcut like Hawaii's; country outline into `state_outline.json`; every "California, Nevada and ..." string; ZIP copy. `venues.json` is 3.2 MB for 14,201 venues (about 225 bytes each); 2,000-5,000 Mexican pins add roughly 0.5-1.2 MB, fine for Pages, but if it passes ~6 MB split the file per country.
7. **Language.** Recommended for v1: **English UI, Spanish place and venue names kept as they are, Spanish aliases for search**. Full Spanish UI (i18n of ~15+ strings per screen, the About text, `llms.txt`, the issue form) is a separate ADR after the metro pilot shows people use it. Owner decides.
8. **Chains and facility scans.** The US chain list (LA Fitness, 24 Hour, Life Time, YMCA) does not apply. Mexican equivalents (Sports World, City Club, private "club deportivo" and "unidad deportiva" networks, state sports institutes) must be found and verified in Phase 2 before any scan.

## Sources (ADR 0005, 0007 unchanged)
Overture + OSM for the base; public pages only for the rest; no Google Places; no partnership or data-license emails; no owner logins (Playtomic and similar are public pages only). Spanish research targets for events, leagues and groups: the national federations (tennis, padel, racquetball, squash, badminton, table tennis, pelota/frontenis; names and URLs to verify in the first pass), state sports institutes and municipal "instituto del deporte" pages, club websites, and public Facebook/Instagram/Meetup group pages. Login-walled pages are leads, not sources (ADR 0027). Record searches and empty results in a Mexico section of `docs/event_group_search.md`.

## Decision (proposed): automatic everywhere, hand-built parity at the border only
Parity (walls, frontenis/handball, events, social, leads) is built for the border pilot metros; the rest of the country gets the automatic OSM + Overture layer only, labelled as such. The "full CA parity" rule is read per covered metro, not per Mexican state. The six core metros (Phase 3) are not scheduled: each is added one at a time, only when GoatCounter or Trends show demand for it (owner 2026-11-04).

| Phase | What | Sessions (est.) |
|---|---|---|
| 0 | This ADR and the owner's answers | 1 |
| 1 | Generalize for a country: `MX` region, boundaries via Overture divisions, country filter in the address extractor, Spanish terms and aliases, app shortcut/outline/copy, CI fixture rows and border test points. No new data. | 3-4 |
| 2 | Border pilot: Tijuana, Mexicali, Ensenada, then Sonora (Hermosillo, Nogales, San Luis Rio Colorado). Metro trial extract (minutes), data layer, reverse geocode, review, events/groups pass, padel and frontenis pass, chain list for Mexico. | 6-8 |
| 3 | **Deferred, demand-gated.** Six core metros, one at a time when usage data asks for it: CDMX (largest, about 8 sessions), Guadalajara, Monterrey, Cancun/Riviera Maya, Merida, Queretaro (about 4-5 each). | 25-30 if all were done; not scheduled |
| 4 | Rest of the country, automatic layer only: nationwide extract, quality scorecard per metro, a coverage note; hand research only where GoatCounter or Trends show demand. | 2-3 |

Scheduled total (Phases 1, 2 and 4): about 11-15 sessions, with Phase 0 already done. The original plan with all six core metros was 37-46 sessions, versus about 250-380 for 32-state parity. Extract time: OSM tiles for the whole country are mostly ocean and desert, so assume a full run at 30-45 minutes (CA+NV is about 15), after metro trials of a few minutes each.

**Expected pins (ratio, unmeasured).** NV has about 170 pins per million people, CA about 250. Assume Mexico starts at 15-40 per million (10-25% of NV's ratio, because OSM and Overture tag fewer racket venues there): about 2,000-5,000 nationally, 550-1,500 in the six core metros (about 37 million people), 100-300 in the border pilot. The trial replaces this with a measured number.

## Cost
- Hosting, data sources and CI stay $0 (running costs doc). Extra raw data in the private raw-data repo and the 10% `load_raw.py` shrink guard are unaffected by adding rows.
- Agents: the only capped spend ($20/month, $5/week, ADR 0019). Routines (tournaments, discovery, refresh agent, search interest) each need Mexico source lists added only after that metro's research exists, as ADR 0028 says. At about $1.50 a run and two refreshes a month (about $3), assume +30-50% page reads for Spanish sources, about $4-5 a month: under the cap. Research sessions themselves are not API spend.
- Search interest (`search_metros.csv`): Mexican metros need Google Trends geo codes and Spanish queries; lowest priority.

## Order and conflicts
Arizona touches the same files as Mexico Phase 1 (`regions.json`, the dbt `regions` var, app bounds, outline, ZIPs, copy), and two PRs on generated files collide (CLAUDE.md). Recommended order: Arizona data layer merged first, then Mexico Phase 1. Phase 1 is code only and can start before the December beta; Phase 2 research waits for the owner's call on beta timing. Phase 3 has no date: it follows demand.

## Owner answers (2026-11-02, in chat)
1. **Language:** English UI with Spanish aliases for v1; Spanish UI is a later ADR.
2. **Parity:** per chosen metro, not per Mexican state.
3. **Resorts (Cancun/Riviera Maya, Los Cabos):** case by case. Add resort courts that are publicly bookable by non-guests; flag the rest for the owner (a different rule from Nevada's closed list).
4. **Timing:** Phase 1 starts after Arizona merges (same files); Phase 2 research waits for the owner's call after the December beta.

5. **Metro order, if Phase 3 is ever run (owner left it to the agent):** Monterrey, Guadalajara, Cancun/Riviera Maya, Mexico City, Merida, Queretaro. The two mid-size metros come first to settle the Spanish-source routine before Mexico City's roughly 8 sessions; Cancun comes third so the resort rule (case by case) is applied once, early.
6. **Repo and Pages naming:** rename after the beta, as already planned (ADR 0028); Mexico changes nothing, since RacketConnect has no region in it (ADR 0029).
7. **Tijuana metro trial:** yes. The OSM and Overture trial for Tijuana (minutes, no commit) may run once Phase 1 is approved.

8. **Scope cut (2026-11-04, in chat):** 37-46 sessions is too many. Build Phases 1, 2 and 4 (about 11-15 sessions: country generalization, border pilot, automatic layer for the rest). The six core metros become demand-gated and unscheduled.

## Built so far
Phase 1 started 2026-11-04: `MX` region (OSM relation 114686; `overpass.border` closes the relation's 17 m Rio Grande gap), six border-pilot metros, dbt var, outline and border test points. `"defer": true` keeps MX out of `make extract` and the Overture default until Phase 4. Tijuana OSM trial: 77 courts (62 tennis, 10 pickleball), 3 named. Spanish search terms and aliases added, and the name normalizer now folds accents (dbt and extractor), so "Pádel" matches "padel". Overture places trial for all of Mexico: 1,246 kept (351 tennis, 105 squash, 52 racquetball), 15 in the Tijuana box, 89% with a street address, 32% with a website; bare "tenis" stays ambiguous because it also catches sneaker shops. Address points: the extractor's country filter now comes from `regions.json` (`country`, default US). Overture has them for Mexico: 377k in the Tijuana box (208k with a house number, source `mx/countrywide`), street names in capitals. Before any MX address is shipped: check that source's licence, and format MX lines as street then number (the US order is number then street). Open in Phase 1: Overture divisions boundaries, app shortcut and copy.

## Still open
What counts as "demand" for starting a Phase 3 metro (a GoatCounter or Trends threshold) is not set; decide it when the first metro is proposed. The ADR stays proposed until the owner says "ship it" on the PR.

## Consequences
Roughly doubles the covered population again with a second language, and coverage will look thin at first (hand-checked only at the border, automatic elsewhere, including Mexico City until demand says otherwise), so the scorecard must report per metro and the app must say "automatic data only" where nothing was hand-checked. One `MX` region keeps the pipeline unchanged for the five US states; splitting Mexico into per-state regions later stays possible through the `subregion` column.
