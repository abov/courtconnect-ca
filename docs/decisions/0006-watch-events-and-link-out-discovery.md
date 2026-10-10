# ADR 0006: "Watch a match" events, and a link-out model for booking, clinics and open play

**Status:** watch events built; link-outs to BracketSync built (hand-curated); Playtomic and PlayByPoint researched, not built

## Context
The product is a **discovery tool**: it helps people find what they want, then sends them to the venue's or organizer's own site
or service to watch or play. It is not a booking system. Two things follow:
1. Watching (pro and amateur matches, tournaments) needs an events layer, and a place to see it.
2. Booking, clinics, private lessons, open play and social events live on other platforms (the plan named Playtomic, PadelUp and
   BracketSync). We should link to them, not reproduce them.

## Decisions
1. **Watch events are curated link-outs.** `transform/seeds/watch_events.csv` holds one row per event: sport, level, how you can watch
   (`in_person_ticketed`, `in_person_free`, `in_person_unconfirmed`, `watch_party`, `dome_screening`, `broadcast_only`), place, dates,
   what is known about tickets, and **the organizer's own links**. Nothing is sold or reserved here; the page says so.
2. **Every fact carries its source and a `verified_on` date.** Dates are `confirmed` or `dates_not_confirmed`. Venue pins are labelled
   when they are only the city centre (the PPA schedule lists no venues). Tests fail the build on a bad coordinate, an end before a
   start, a non-https link, or an event with no official link; a warning fires when an upcoming event has not been re-checked in 120 days.
   The browser also hides events whose end date has passed, so a stale deploy does not show old events.
3. **Provider data comes only through permitted routes.** No scraping. After the Google Places lesson (ADR 0005) each source's terms are
   checked first. Where no permitted feed exists, we store a provider name and a deep link, which needs no data from them.

## What the research found (2026-10-09)
- **Playtomic:** its help centre says outside companies integrate through **Playtomic Connect** (an application plus a qualification call),
  and that clubs on higher plans can create their own read-only API credentials for booking data. It also says unauthorized
  third-party access is being restricted. There is no public discovery feed to pull from, so the route is a partner application, or links only.
- **"PadelUp":** the match I found is **Padel Up**, a Los Angeles padel club (Century City and Culver City) whose events and bookings run on
  **PlayByPoint**. I found no standalone PadelUp app.
- **"BracketSync":** I could not find a platform by that name. If you have its URL, its terms are the first thing to read.
- **Events:** the official PPA Tour schedule page lists five California events with dates but no venues or ticket details; the BNP Paribas
  Open's official site gives dates, venue and ticket types. Those six events are the seed. Pro Padel League's last California event (Santa Monica, Aug 2026) has passed.
  I found no verified "interactive dome" screenings, so `dome_screening` exists as a format but has no entries.

## BracketSync (read 2026-10-10)
- **What it is:** a tournament, league and classes app for racket and paddle sports, run by MetaPaddles, LLC. Its public pages list
  clubs, tournaments and leagues; 10 California clubs are on it (beach tennis, paddle tennis, pickleball). The only California events listed
  today are Beach Tennis Cali Club's leagues.
- **Terms:** two short pages. They say nothing about reusing its data, document no API, and say people keep ownership of what they post.
  Event pages are a JavaScript app with no sitemap or `robots.txt`. So nothing is copied in bulk, and no undocumented API is called.
- **Decision:** link out. We store the provider, a deep link to the club or event page, the dates and price note shown there, and a
  `verified_on` date. We do not collect its player leaderboards (named individuals).
- **Next step:** ask MetaPaddles (the contact is on its terms page) whether it offers a feed or partner access for California events.

## Hand-added venues are merged, not duplicated
A hand-added venue within 150 m (`manual_match_radius_m`) of a court or place we already hold is **merged into it**
(`int_manual_venue_match`), enriching its name, access and offerings; otherwise it stands alone. A test fails the build if an entry
would vanish. Limit: a venue whose address is at the edge of a big park can land beyond 150 m and stay separate, so a park can still show
two pins (for example a tennis court from OpenStreetMap and a hand-added paddle tennis court).

## Built
Six California events (BNP Paribas Open; PPA stops in Malibu, Rancho Mirage, Newport Beach, Sacramento, San Clemente), a `mart_watch_events`
model, and a **Watch a match** mode in the map app with date-ordered list, event pins, and link-outs.

## Not built (next)
- **More `venue_actions`**: so far 4 BracketSync links. Next: clinics, private lessons and open play from each club's own site, and Playtomic / PlayByPoint
  once a partner route exists. Clubs on BracketSync with no known court location (e.g. SoCal Pickleball in Burbank) cannot be pinned yet.
- A broader events source (a ticketing-search API with a free key; check its caching and display terms before storing anything).
- Event sources are thin on purpose: six confirmed events beat sixty unverified ones.
