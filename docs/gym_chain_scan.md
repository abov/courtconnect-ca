# Gym chain court scan (CA + NV) — plan

Goal: add courts that gyms and athletic clubs host (racquetball first; also squash, pickleball, tennis, basketball is out of scope) and that the map misses. Why they are missing: the Overture extract keeps only racket-category places, so gyms never enter the pipeline (checked 2026-10-14: no LA Fitness on the map; 21 CA + 8 NV Racquetball venues).

## Rules
- Evidence = the chain's own public club page listing the sport, read by script or by hand. Record the page URL in `evidence`, `confirmation=official`, `confirmed_on` = read date.
- No Google Places data (ADR 0005); do not copy the USA Racquetball court list (terms, see `venue_leads.csv`); no logged-in pages (ADR 0007).
- Chain pages say amenities "may not be available at all locations": a club is added only if its own page lists the sport. Court counts only if the page states them.
- Access: `members` for membership gyms (inferred, say so), unless the page says otherwise.
- Throttle to ~1 request per 0.4 s; descriptive User-Agent; stop if a site blocks us.
- Positions: Nominatim geocoder (1 request/s, as `ingestion/import_paddle_tennis_map.py`); record how each was placed in `location_precision`.

## Per-chain checklist (one chain per session)
| # | Chain | Source to check | Status |
|---|---|---|---|
| 1 | LA Fitness | `lafitness.com/Pages/clubhome.aspx?clubid=N`; address in `#clubInfoAddress`, amenity list incl. `Racquetball*`. Scripted scan works (200 OK, no robots.txt). | scan started 2026-10-14 (`ingestion/scan_lafitness.py`); results not yet imported. Torrance 3550 W Carson St looks closed (Yelp), Harbor City (clubid 620) lists racquetball |
| 2 | 24 Hour Fitness (Super Sport) | club pages on 24hourfitness.com; many courts removed after 2020, so check each page | todo |
| 3 | Bay Club | `bayclubs.com/amenity/racquetball` lists clubs (Pleasanton, Redondo Beach, Manhattan CC already on map, SF) | todo |
| 4 | ClubSport (Aliso Viejo, Pleasanton), Life Time, Equinox, Sports Club LA, Gold's, Crunch, Town Sports | each chain's club pages | todo; Life Time CA clubs found so far list pickleball/tennis, not racquetball |
| 5 | YMCAs, city rec centers, universities, military (MWR) | city/Y facility directories (Henderson leads already in `venue_leads.csv`) | todo, hand work |
| 6 | Nevada | LA Fitness, 24 Hour, Life Time, Henderson/Las Vegas rec centers, Red Rock Resort, Boulder Station-type casino gyms | todo |

## Session recipe
1. Scan the chain's club pages to a scratch CSV (id, name, address, phone, sports listed). Keep only CA/NV rows that list a sport this project covers.
2. Skip clubs already on the map for that sport (match by address/name in `marts.mart_venue_finder`).
3. Geocode, write rows to `manual_venues.csv` (CRLF endings!) and a `venue_actions.csv` link-out to the club page (keep `verified_on` + `evidence`).
4. `dbt build --select` narrow check, then full build once; `make app-data`; commit `app/data/venues.json`; re-run `pages.yml` after merge.
5. Record closed/unclear clubs in `venue_leads.csv`, update the table above and "Current status".

## Open questions
- Should gym courts be on the map by default or behind a "gyms/clubs" filter? Decide with the owner after chain 1 (could be hundreds of pins).
- Add an Overture gyms extract (`fitness_center`) so chain gyms are discoverable for matching and review? Needs an ADR; do after chain 1 if matching by address proves painful.
