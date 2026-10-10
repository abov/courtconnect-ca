# ADR 0006: "Watch a match" events, and a link-out model for booking, clinics and open play

**Status:** watch events built; link-outs built for 2 beach tennis clubs and 6 padel clubs (hand-curated from the clubs' own sites); Playtomic and PlayByPoint read, link-out only

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

## Clubs' own sites (read 2026-10-10)
Beach Tennis Santa Monica and BT Cali Club publish their programs on their own sites, so those are the sources for 18 more link-outs
(open play, drop-in and group classes, kids classes, semi-private training, a league, tournaments). Findings worth knowing:
- **BTCC's site lists no open play, clinics or private lessons.** Its Yelp listing mentions private classes; the owner reported open play and
  clinics. None of that is on the club's own pages, so it is not shown. The site does list a $10 trial class, class matching, a league and a
  Halloween tournament (Oct 25, Hermosa Beach, $50 / $40 members).
- **Both clubs use the same public beach courts** (7th St Manhattan Beach, 14th St / The Strand Hermosa Beach), so those two venues are now
  named by place and each club's programs appear under them with the club named in the title. Before, the venue carried one club's name.
- **BTSM's own pages disagree with themselves** on Hermosa open play (free first-come courts vs a $10 walk-in price); the row shows both
  and says to confirm. Its league page still shows sign-up open two months into the season.
- **Not found:** SoCal Pickleball (Burbank), Hélio Amorim Beach Tennis (San Diego), San Francisco Beach Tennis and Ricardinho BT have no
  findable website, program or court location, and Pop Paddle Venice's open-play details exist only on third-party aggregators. Nothing was
  guessed; they are not on the map beyond what is already there.

## Playtomic and PlayByPoint (read 2026-10-10)
- **Playtomic:** its `robots.txt` disallows crawling `/api`, `/tournaments/*`, `/activities/*`, search pages and query-string listings, which are exactly
  the open-play, class and tournament pages. Club pages (`/clubs/...`) are not disallowed. Playtomic Connect is for companies integrating with club
  systems under a certification agreement; its page does not say whether discovery sites qualify. So: no crawling; we link to a club's Playtomic page only
  when the club's own site links there.
- **PlayByPoint:** `robots.txt` blocks only reservations and user pages. Its Terms of Use are short, govern its users and the clubs on it, and restrict
  copying or reverse-engineering the *software*; they do not mention scraping or an API. No ban, but no grant, so the same rule applies: read a club's pages
  one at a time as a visitor, store only links and the facts the club itself publishes, never bulk-crawl.
- **Where padel programs really come from:** the clubs' own sites. Padel Up books on its own subdomain; Pura Padel and Padel California link to Playtomic;
  The Padel Courts links to PlayByPoint; Park Padel and Bay Padel use their own booking pages. 41 link-outs were added from those sites.
- **Gaps:** Padel Up's site lists no clinics, classes or open play. Bay Padel has more clubs (Dogpatch, Sunnyvale, San Jose) and Padel Up has a Culver City
  club that are not on the map yet. San Diego NOX Padel Club has no usable website (see below). Other tennis clubs with a few padel courts were not read.

## Data-quality finds from this pass
- **Parked domain:** `sandiegopadelclub.com` (our San Diego NOX Padel Club listing) is a GoDaddy parked page. DNS resolves, so the website check could not
  see it. `seeds/website_overrides.csv` now lets a person flag such sites as dead; the override wins over the automatic check.
- **Bad place record:** "Sunset Padel Sports Club" (Los Angeles) carried a Miami Beach club's website and sits at the same address as The Padel Courts. Rejected for
  Padel in `place_sport_overrides.csv`.

## Platform tennis in California
No source we hold (OpenStreetMap, Overture) lists a platform tennis court in California. A Platform Tennis Hall of Fame article (Platform Tennis Magazine, Vol. 16
Issue 2, 2014) says all of California's platform tennis courts are in **Ross, Marin County**: three at **Lagunitas Country Club**, one public court in town and
a couple of private courts. Lagunitas Country Club (205 Lagunitas Rd, Ross) is on the map as an **unconfirmed lead**: the 2014 court count is not shown as
current, public access is marked not confirmed, and the club's site (a members' site) says nothing about platform tennis. To confirm, call the club, the Town of
Ross, or APTA.

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
