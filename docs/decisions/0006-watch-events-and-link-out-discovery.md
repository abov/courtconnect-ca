# ADR 0006: "Watch a match" events, and a link-out model for booking, clinics and open play

**Status:** watch events built; provider integrations (booking, clinics, privates, open play, social) researched, not built

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

## Built
Six California events (BNP Paribas Open; PPA stops in Malibu, Rancho Mirage, Newport Beach, Sacramento, San Clemente), a `mart_watch_events`
model, and a **Watch a match** mode in the map app with date-ordered list, event pins, and link-outs.

## Not built (next)
- **`venue_actions`**: per venue, links to book a court, join a clinic, take a private lesson, find open play, or sign up for a tournament,
  each with provider, URL and `verified_on`. Fill it by hand first, then from partner APIs once access is granted.
- A broader events source (a ticketing-search API with a free key; check its caching and display terms before storing anything).
- Event sources are thin on purpose: six confirmed events beat sixty unverified ones.
