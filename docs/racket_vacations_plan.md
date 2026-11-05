# Racket sport vacations chip (draft)

Drafted 2026-11-05 from the owner's idea in chat: a separate top-level chip for racket sport vacations. Nothing here is built; the Mexico rows are unverified leads from search results.

## Proposal

- **Chip:** a third mode beside "Places to play" and "Events & meetups" (`index.html`, the `modePlay` / `modeWatch` pattern; `#mode=trips`). It shows vacation pins on the map and a list below, filterable by sport, link-out only (no bookings, ADR 0007 rules unchanged).
- **Data:** new seed `transform/seeds/racket_vacations.csv`, one row per offer, exported to `app/data/vacations.json` (like `watch_events.csv` -> events). Columns: `vacation_key, name, kind (resort | camp | academy | tour), destination, country, lat, lon, sports, who_can_play (guests | anyone | booking), price_note, info_url, evidence, verified_on, status (verified | lead)`.
- **Honesty:** only `verified` rows (own page or a dated news item, with `evidence` + `verified_on`) show; `lead` rows stay in the seed. Same bar as the border pilot.
- **Not a duplicate of venues:** a resort's courts can stay a venue pin (as in `docs/hawaii_resorts.md`); the vacation row is the trip framing (stay + play, camps, clinics) and links to the venue where one exists.

## Decisions

1. **Scope (owner, 2026-11-05):** regions already on the map only; no worldwide destinations yet. Recorded in ADR 0036 (proposed).
2. **Resorts.** The case-by-case resort rule applies: list what non-guests can book, flag guests-only (`who_can_play`).
3. **Chip label:** open. "Racket vacations" unless the owner prefers "Trips".

## Unverified Mexico leads (search results 2026-11-05, not yet read at the source)

| Lead | Where | Sports (as reported) | Source |
|---|---|---|---|
| Hard Rock Los Cabos | Los Cabos | Pickleball, 4 courts | [Visit Los Cabos](https://www.visitloscabos.travel/blog/post/ace-your-next-getaway-with-los-cabos-thriving-court-sports-scene/) |
| Montage Los Cabos | Los Cabos | Pickleball, free courts and clinics | same |
| Club Med Cancun | Cancun | Pickleball | [Club Med](https://www.clubmed.us/l/pickleball-cancun) |
| Mayakoba | Riviera Maya | 4 tennis, 1 pickleball | [TravelAge West, Nov 2023](https://www.travelagewest.com/Travel/Mexico/where-to-play-pickleball-in-Mexico) |
| Sandos Caracol Eco, Sandos Playacar | Riviera Maya | Padel and pickleball (opened 2024) | [Sandos press release](https://www.sandos.com/sites/default/files/2024-05/Playacar%20and%20Caracol%20Pickleball%20Courts%20Press%20Release%20_0.pdf) |
| Villa del Palmar | Puerto Vallarta | Pickleball | [Villa del Palmar](https://vallarta.villadelpalmar.com/blog/news/spend-a-great-day-playing-pickleball) |
| Four Seasons Punta Mita | Punta Mita | Tennis | [Tennis Resorts Online](https://tennisresortsonline.com/places/four-seasons-resort-punta-mita-mexico/) |
| All4Padel Playa | Playa del Carmen | Padel, 4 courts | [Padelbrowser](https://www.padelbrowser.com/clubs/directory?states=ROO) |

Beach tennis: no Mexican club found in two searches (Cancun, Playa del Carmen, Tulum, Los Cabos). Not searched in Spanish yet ("tenis de playa").

## Out of scope for now: destinations off the map (from general knowledge, unchecked; revisit after the December beta)

Beach tennis camps (Italy's Adriatic coast, Brazil, Spain, Portugal), padel camps (Spain, Algarve, Dubai), tennis resorts (Palm Springs, Scottsdale, Hilton Head), pelota and frontón (Basque Country).

## Build order (each a separate PR)

1. ADR 0036 (drafted).
2. Seed + staging/core model + tests + `make app-data` export (no UI).
3. Chip, map layer and list, with `#mode=trips` share links.
4. First verified batch: Mexico resorts above, then Hawaii.
