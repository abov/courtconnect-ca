# Public facility scan (cities, counties, parks) — plan

Goal: find racket-sport courts run by cities, counties, school districts and park agencies in CA + NV that the map misses: tennis, pickleball, pop tennis, racquetball, squash, table tennis, badminton, beach tennis, and any other racket sport in `all_racquet.csv`. Complements `docs/gym_chain_scan.md`.

Pilot (2026-10-14): Hawthorne Sports Center. The city page lists adult racquetball ($8/h, Mon-Fri 3-9 pm, Sat 8 am-5 pm, reserve up to a week ahead) but no court count or street address. It is not on the map (Hawthorne only has Jim Thorpe Park). Lead added: `hawthorne-sports-center`. Note `cityofhawthorne.org` returns 403 to WebFetch/curl; the browser pane reads it as text.

## Why this is harder than chains
No standard page layout: ~480 CA cities + NV cities/counties, each with its own site, and many give 403 to scripts. Expect hand reading for most, scripts only for the few platforms shared by many cities.

## Sources, cheapest first
1. **Platform directories many agencies share** (one scraper, many cities): Civic Rec / ActiveNet / CivicPlus "facility directory" pages (Henderson uses one), Recreation.gov (federal), county park GIS open data (LA County, SD County, Clark County, Washoe) that carry facility + amenity lists under open licenses. Check each license; prefer official open-data portals.
2. **OpenStreetMap**: city parks already ingested; gap is facilities mapped as a building (`leisure=sports_centre`, `sport=racquetball` etc.). Query Overpass for sports centres/community centres in CA+NV with any racket `sport=*` tag not yet matched. Cheap; fix OSM too (`docs/contribute_to_osm.md`).
3. **Overture**: add categories `recreation_center`/`community_center`/`sports_and_recreation_venue` to the extract so public facilities become matchable places (needs an ADR; do together with the gym `fitness_center` decision).
4. **City site search by hand**: for each city with a population above ~50k, read the "parks and facilities" / "recreation" pages in the browser pane and note racket sports. ~150 cities; do in batches of ~15 per session, biggest or most-requested first (LA County South Bay, SD, Bay, Sacramento, Las Vegas, Henderson, Reno).

## Rules
- Evidence = the agency's own public page; record URL, `verified_on`, `evidence`. Counts only if the page states them. Fees/hours go in `offerings`/`rules` only if stated.
- No Google Places data (ADR 0005), no logged-in/reservation-account pages (ADR 0007), do not copy aggregator lists (USA Racquetball WOR list, Pickleheads, Bounce terms) into the database.
- Access `public` or `reservation` only if the page says so; otherwise leave unconfirmed.
- Locations: street address -> Nominatim (1 req/s); record how placed in `location_precision`; no address -> lead, not a pin.
- Throttle scripted fetches (~0.4 s/request, descriptive User-Agent); stop when a site blocks us and switch to the browser pane.

## Sessions (one per step)
1. Hawthorne pilot: get address + court count, add manual venue + link-out. Run the OSM sports-centre query (source 2) and list gaps. Decide on the Overture categories ADR (source 3).
2. Platform directories (source 1): inventory which cities/counties use a shared platform and which open-data portals exist; scrape the first one.
3-N. Hand pass by region (source 4), ~15 cities per session; log unreadable/403 sites in `venue_leads.csv`.

## Estimated cost
Session 1: small. Session 2: moderate (research). Each hand pass: moderate, mostly browser-pane text reads (no screenshots). Do not run all regions at once.
