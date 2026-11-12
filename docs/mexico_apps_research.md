# Mexico racket-sport apps: research notes (2026-11-11)

Research only, public pages (App Store listings, club pages, federation and press pages). No logins, no directory scraping, no emails to any app (ADR 0005/0007, owner 2026-10-16). Nothing here is a seed edit. Venue and metro detail already lives in `docs/event_group_search.md` ("Mexico: ..." sections) and `docs/mexico_metro_trial.md`; this note adds the app layer on top.

## Headline

- **Playtomic is the only app that matters at scale.** The others are small, new (2025-26), single-club or white-label tools. Almost every Mexican padel pin already links out to a Playtomic club page.
- **The apps are padel-first.** No app found covers racquetball, frontenis, table tennis or badminton in Mexico; those sports run on federation pages, state "Olimpiada Nacional" notices and club Facebook pages.
- **Public app pages expose little about events.** A Playtomic club page shows courts, hours and amenities; tournaments and leagues sit in the app. So events come from federation, press and club sites, not from the apps.

## Apps

**Playtomic** (Spain; padel, plus tennis and pickleball listings). Clubs: private padel clubs, hotels, multi-sport clubs, Wellhub-type gyms. Public club page (`playtomic.com/es/clubs/<slug>`): description, map point, amenities ("Comodidades"), hours ("Horario de apertura"), "Deportes disponibles", nearby clubs; no club website link and no dated events in the readable page (tested on Baaxal Pádel México). In the app and in Playtomic's own plan pages: public classes ("clases"), leagues ("ligas"), tournaments, memberships, "Americanas/Mexicanas" social formats, ranking. Popular in CDMX, Monterrey, Guadalajara, Querétaro, Mérida, Cancún (the six metros all have Playtomic-sourced pins). US: Playtomic says it works with over 60% of US padel clubs; its US push is Florida and Texas, and no CA/NV/OR/WA/HI/AZ detail was found (check the club pages for our states before relying on it). Link from a venue: the club's own site or Instagram often has a "Reserva" button to its Playtomic page; we link the Playtomic page directly.

**Mexico Padel** (App Store, 2025; multi-club padel app powered by Bookandgo, a white-label booking platform). Books courts across affiliated clubs, matchmaking by level, tournaments and events. Book & Go sells each club a branded app and back office (courts, classes, lessons, open matches, tournaments, memberships, 0% commission). Club count and city split not published; the App Store text gave no list. A Bookandgo page for Mexico City padel and pickleball exists. Venue link: through the club's own branded app or the Mexico Padel listing; no stable public per-club URL confirmed.

**PadelMatch** (App Store, v1.0 in early 2026, developer Diego Rubio Ochoa, 3 ratings). Court booking with CentumPay, player profiles with levels (Novato, Intermedio, Avanzado, Pro), tournaments with elimination brackets and check-in, manager dashboard at manager.padelmatch.fit. No cities or clubs named. Treat as a startup to recheck, not a source.

**Smart Padel** (App Store, iPhone only, Mexico listing; a same-named Latvian/Portuguese app also exists, don't confuse). Booking, tournaments, "pozos" (pot or winner-stays formats), gear store, plus club-admin tools (courts, users, tournaments, finances). No club list public.

**Baaxal** (App Store; "Baaxal Pádel México"). This is one club group's own app (Baaxal Pádel México in Huixquilucan/Naucalpan, 5 courts, and Baaxal Bosques in CDMX), for booking and logging matches, events and classes. Not a marketplace. Both clubs also have Playtomic pages. It shows the pattern: a club ships its own app and also sits on Playtomic.

**AlquilaTuCancha** (Argentina; Uruguay-born booking marketplace; listed as available in Argentina, Chile, Peru, US, Panama, Uruguay and Mexico). Search by city, sport, date; pay a deposit or none, per club. No Mexican venue evidence found; Spanish terms "alquilar una cancha", "seña". Low priority.

**Arosports:** no app, site or club page by this name was found by search. The only repo evidence is Triple Diamante Club de Pádel (Corregidora, Querétaro), whose own site says to book "in the Arosports app" (25% deposit). Ask what the owner means before spending more time; if it is that app, its public footprint is a club-site link only.

**Others seen (not asked for):** Padel Mates, MATCHi (padel, tennis, badminton, table tennis, pickleball, squash; Europe-heavy), OpenCourt (tennis, pickleball, padel), PlayByPoint (US and other markets; padel and other racket sports), Pala (tournaments, finding players), Padelmit (match finding), Cancha - Reserva tu jugada (generic court booking, sports not stated), Reservadeportes and AQQO (club software), Gestión del Deporte Saltillo (a city sports-booking app), Wellhub and TotalPass (gym passes: their partner pages named several pins in earlier passes; access is "plan", not "public", so state access unknown).

## Other racket sports: nothing app-based

- **Pickleball:** Pickleheads and Pickleball Plus directories are off limits (data). Public: The Pickle Co, PBMX and Pickleball Santa Fe sites (CDMX), CDMX Pride Meetup, Claro Sports coverage of the Pickleball Tour (stops: Puebla, Monterrey Aug 2025, San Carlos Sonora Dec 2025), Americas Pickleball Cup (Cozumel, April 2026, past). No Mexican federation page found in search.
- **Raquetbol:** Federación Mexicana de Raquetbol events via dailyracquetball.com and proracquetballstats.com (2026 junior nationals San Luis Potosí; Monterrey Open at Club Deportivo Cumbres).
- **Frontenis / frontón / pelota:** Torneo Nacional Abierto de Frontenis 2026, Puebla (Milenio); Olimpiada Nacional frontón technical annexes (state notices); city sports institutes.
- **Tenis de mesa:** FMTM Mexican Open at CAR Tijuana; INDE selectivo notices (youth state teams).
- **Bádminton:** only Olimpiada Nacional rules and club courts (CAR Tijuana, Parque Asturias, Centro Deportivo Chapultepec). No federation calendar found.
- **Tenis:** FMT (tenisfmt.com; calendar is script-driven and unreadable as text), ITF and WTA pages, state associations.
- **Padel federation:** FEMEPA (femepa.app; 2026 rulebook PDF found, ranking tournaments, national championship at Épica Mérida April 2026; no readable 2026 calendar). International: Premier Padel Cancún P2 (Mar 2026), Mexico Major in Acapulco (out of scope), CUPRA Pádel Tour stops (Guadalajara Apr, Monterrey Sep, Querétaro Jul 2026), Pro Padel League.

## Spanish vocabulary (for search terms, `rules`, event titles)

- Court: **cancha** (tennis, pickleball, raquetbol, frontón), **pista** (Spain; Playtomic's es pages use "pista", Mexican clubs say "cancha").
- Sports: pádel, tenis, pickleball, squash, raquetbol, frontenis, frontón, pelota vasca, tenis de mesa / ping pong, bádminton.
- Formats: **torneo**, **liga**, **americana** (rotating partners, social), **mexicana** (variant of americana), **pozo** (winner-stays), **reta** (pickup game, Mexican), **sparring**, **ladder/escalera**, **ranking**, **categoría** (levels: Novato, Intermedio, Avanzado, Pro; or 1a-6a fuerza, "libre").
- Learning and booking: **clase** (class), **clínica**, **academia**, **escuela**, **entrenador/profesor**, **reservar/reserva**, **membresía**, **socio**, **solo socios** (members only), **abierto al público**, **renta de cancha**, **seña/anticipo** (deposit), **inscripción** (entry).
- Places: club deportivo, unidad deportiva, deportivo, club campestre, centro deportivo, polideportivo, CODE/INDE/IMDET (state or city sports institutes), CAR (Centro de Alto Rendimiento).

## Where each app is popular and what a venue page links to

- **CDMX, Monterrey, Guadalajara, Querétaro, Mérida, Cancún:** Playtomic dominates. Border metros: Playtomic plus AppPadel (Tijuana Padel). Querétaro: Arosports (one club). Mexico Padel / PadelMatch / Smart Padel: no confirmed club in any metro from public pages.
- **US overlap:** Playtomic is the same app in our US states; a US padel pin and a Mexican one use the same link-out type. Border metros overlap with CA and AZ (Tijuana/San Diego, Mexicali/Calexico, Nogales, San Luis Río Colorado/Yuma): the same player may use a US and a Mexican club, which supports a "nearby across the border" view, not any data merge.
- **Public link patterns:** a club site or Instagram bio carries a Playtomic or app-store button; Playtomic club pages carry no website field. So the club's own site is the evidence for operator links, and the Playtomic slug is the evidence for court counts.

## Venue and event leads by metro (ADR 0034 order)

All of these are already pins or logged leads from earlier passes; evidence and dates are in `docs/event_group_search.md`. New or still open:

- **Monterrey:** Abierto GNP Seguros 2027 (Club Sonoma, Aug 22-28, in watch events); open leads: FMR Monterrey Open 2027 (dailyracquetball.com), CUPRA Pádel Tour (Sep), Pickleball Tour stop, CARE Niños Héroes public use (INDE Nuevo León, phone 81 8601 8875 per Posta), Playtomic slugs `padel-gm-san-nicolas`, `sky-racquet` (404).
- **Guadalajara:** Guadalajara Open 2027 (Sep 12-18, in watch events); Pro Padel League return (propadelleague.com); CUPRA Pádel Tour (Padel Sport); COMUDE Zapopan and Asociación de Tenis de Jalisco calendars; Athletes Lab weekly "retas" (Playtomic text, no dates).
- **Cancún / Riviera Maya:** Premier Padel Cancún P2 2027 date (premierpadel.com), FIP Junior America Cup Nov 10-14 2026 host club (padelfip.com), Quintana Roo state padel circuit, Playa del Carmen Pickleball Club (Facebook/WhatsApp only), Pro Padel League Playa del Carmen.
- **Mexico City:** Mexico City Open (ATP Challenger, Centro Deportivo Chapultepec; recheck January 2027), The Pickle Co /ligas season 04, CDMX Pride Meetup dates, Piong Club (table tennis, 2023 source only), Go Padel Club Tecámac map point, racquetball clubs (none found).
- **Mérida:** Mérida Open 2027 (Feb 22-28, in watch events), Copa Mundial Yucatán 2026 (ITF J500, Nov 23-28, page unreadable), EK Padel Club Saturday opens, next FEMEPA national championship, Asociación de Pádel del Sureste.
- **Querétaro:** Querétaro Open 2027 dates (wtatennis.com/tournaments/1145), CUPRA Pádel Tour (FEMAC Pádel Club unlocated), Triple Diamante / Josefa Pádel open-play retas (WhatsApp).
- **Border/US overlap:** CAR Tijuana FMTM Mexican Open (Feb), Club Campestre de Tijuana tournament (Sep), IMDET 2027 calendar (December), Rosarito women's tennis (dates unconfirmed), Smash Pickleball and Hermosillo padel clubs (Instagram only).

## Mapping to the mission

- **Find a court:** Playtomic club pages (court list with walls and cover, hours) are the best public source and are already the evidence behind most pins. Booking itself is link-out only.
- **Watch a match:** not from apps; from WTA/ATP/Premier Padel/Pro Padel League tournament pages (`watch_events.csv`, https only).
- **Try a sport:** club classes ("clases", "academia", "clínica") and open-to-public pickleball (The Pickle Co, PBMX); Wellhub/TotalPass partner pages say which sports a gym has but not whether non-members can play.
- **Find people to play with:** app features (open matches, level matching, americanas, retas) are login-gated and stay in the apps. Our public equivalents are Meetup groups, club WhatsApp links published on club sites, and `social_events.csv` series. Link out to the app; don't copy player data.

## Link-out fields that would help `venue_actions.csv`

Current columns: `action_key, venue_ref_type, venue_ref, action_type, title, provider, url, price_info, start_date, end_date, evidence, verified_on`. These fit already; suggestions are values, not new columns:
- `provider` values to standardize: Playtomic, Mexico Padel, Arosports, AppPadel, Wellhub, TotalPass, club site, WhatsApp, Instagram.
- `action_type` values worth having for Mexico: booking (cancha), classes (clase/academia), open play (reta/americana), league (liga), tournament (torneo), membership. Mark `price_info` in MXN with the unit ("MXN 300 / 4 h").
- Put the operator or app in `rules`, never in the pin name. Use `evidence` for the club-site button or the Playtomic slug and its read date.
- A separate "access" cue (public, members, guests, Wellhub plan, unknown) is already carried in `rules`; keep it there.
- Worth a future column or action type only if a use appears: `whatsapp` joins for open play (published by the club itself).

## Not done / caveats

- App Store pages were read through search snippets and one fetch each; some (Mexico Padel, Smart Padel) returned 404 on direct fetch, so details there come from search text. No download counts or club counts verified.
- No Playtomic US-state club counts were checked for CA, NV, OR, WA, HI, AZ.
- Federation calendars (FMT, FEMEPA, FMR, FMTM, frontenis) were not readable as text; leads above stand until rechecked.
- Pickleheads, Pickleball Plus, Bounce and padelbrowser/padeldir pages were not used as evidence.
