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
| 1 | LA Fitness | `lafitness.com/Pages/clubhome.aspx?clubid=N`; address in `#clubInfoAddress`, amenity list incl. `Racquetball*`. Scripted scan works (200 OK, no robots.txt). | scan done 2026-10-14 (`ingestion/scan_lafitness.py`): 113 CA/NV clubs, 56 list racquetball, raw results in `docs/gym_scans/lafitness_ca_nv_2026-10-14.csv`, 48 imported 2026-10-14 as `lafitness-<clubid>` manual venues (members, inferred); 5 of the 8 street-only clubs placed later from OSM places named LA Fitness; Valencia and E PCH Long Beach placed in round 3; only Hemet stays a `needs_location` lead. No Nevada club in ids 1-1799 (highest id seen about 1250) and the locator page lists none: LA Fitness appears to have no NV clubs (only SEO blogs claim some; unverified). Torrance 3550 W Carson St looks closed (Yelp), Harbor City (clubid 620) lists racquetball |
| 2 | 24 Hour Fitness (Super Sport) | club URLs from `24hourfitness.com/sitemap.xml`; each page has coordinates in its markup and an amenity list (`ingestion/scan_24hour.py`) | done 2026-10-14: 158 CA/NV club pages, 12 list a racquetball court (11 CA, Summerlin NV; also squash at Summerlin), raw results `docs/gym_scans/24hour_ca_nv_2026-10-14.csv`. Sunnyvale (a search result listed a racquetball court) is not in the sitemap scan, recheck by hand |
| 3 | Bay Club | `bayclubs.com/amenity/racquetball` lists Bellevue WA, Redondo Beach (2 courts) and Pleasanton | done 2026-10-14: Redondo Beach + Pleasanton added; Manhattan CC was already there. Bay Club SF/Gateway not on that page, so not added |
| 4 | ClubSport, Life Time, Equinox, Sports Club LA, Gold's, Crunch, Town Sports | club pages | checked 2026-10-14: ClubSport Aliso Viejo added (racquetball + squash; its page timed out intermittently, Walnut Creek is a lead); Life Time: all 13 CA/NV club pages (from their sitemap) mention pickleball and no racquetball; Equinox / Sports Club LA amenity lists show squash or none, no racquetball; Gold's/Crunch/Town Sports not checked (little racquetball expected) |
| 5 | YMCAs, city rec centers, universities, military (MWR) | city/Y facility directories | partly: Henderson, Las Vegas (Chuck Minker), Hawthorne done. North Las Vegas, Sparks, Reno, Carson City: no racquetball on their pages (Carson's own 2010 document says none). Leads: Boulder City Rec Center, Hilltop YMCA Richmond. Still hand work: other YMCAs, university rec centers, military bases |
| 6 | Nevada | LA Fitness has no NV clubs. Done 2026-10-14: Henderson rec centers (5), City of Las Vegas Chuck Minker Sports Complex (5 courts), 24 Hour Fitness Summerlin. Reno/Sparks/Carson/Clark County pages show no racquetball. Still todo: Life Time (Summerlin page states no guest access), resort gyms, North Las Vegas |

## Session recipe
1. Scan the chain's club pages to a scratch CSV (id, name, address, phone, sports listed). Keep only CA/NV rows that list a sport this project covers.
2. Skip clubs already on the map for that sport (match by address/name in `marts.mart_venue_finder`).
3. Geocode, write rows to `manual_venues.csv` (CRLF endings!) and a `venue_actions.csv` link-out to the club page (keep `verified_on` + `evidence`).
4. `dbt build --select` narrow check, then full build once; `make app-data`; commit `app/data/venues.json`; re-run `pages.yml` after merge.
5. Record closed/unclear clubs in `venue_leads.csv`, update the table above and "Current status".

## Open questions
- Should gym courts be on the map by default or behind a "gyms/clubs" filter? Decide with the owner after chain 1 (could be hundreds of pins).
- Add an Overture gyms extract (`fitness_center`) so chain gyms are discoverable for matching and review? Needs an ADR; do after chain 1 if matching by address proves painful.
