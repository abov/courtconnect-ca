# Directories for sports with no venues yet

First pass, 2026-10-10: a general web search per sport for a California club or court directory. Public pages only (ADR 0007).
"No usable directory found" means this search found none, not that none exists. The sport-level lead is not a link-out:
`venue_actions.csv` attaches to a venue, so a directory becomes a link-out only once a venue exists.

| Sport | Result | Next step |
|---|---|---|
| Outdoor Racquetball | Directory exists: USA Racquetball's outdoor court list (https://www.usaracquetball.com/wor/wor-court-list), a spreadsheet of 600+ courts, last updated about 2022. Terms checked in the second pass (below): link out only. | Lead `outdoor-racquetball-wor-list`: do not copy rows. Ask USA Racquetball for written permission, or find courts from other public sources. |
| Soft Tennis | No California club or USSTA-style listing found. Third pass (2026-11-22): the US is only a provisional ISTF member with no club list; see below. | None planned: the 30 mapped Soft Tennis venues are OSM-derived. |
| Crossminton | Governing body is the International Crossminton Organisation (crossminton.org). Third pass (2026-11-22): Crossminton USA exists (Indiana) and so does Crossminton Mexico; neither lists a club or event in our regions. | Stays a play-anywhere sport (ADR 0020); pin only a real club or event with a public page. |
| Frontenis | No California fronton or club found. | Ask Mexican-American and Basque cultural clubs; check pelota federations. |
| Basque Pelota | No California fronton found. | As above. |
| Jai alai | No California fronton found; the sport survives mainly in Florida and the Northeast. | None planned. |
| Hand Tennis | Nothing found under this name (search returned Venice paddle tennis, already on the map). | Ask the owner what it is called locally. |
| Real Tennis | No California court found. Third pass (2026-11-22): the USCTA club list has no court in any covered region. | None planned; recheck the USCTA list at the next quarterly look. |
| Tamburello | No California club found. Third pass (2026-11-22): no US or Mexico club found. | None planned. |
| Touchtennis | Searched on its own 2026-10-10: official site is touchtennis.com, but its venue finder and rules point to the UK section; no US body or California venue list found. | None planned. |

## Second pass, 2026-10-10

### USA Racquetball outdoor court list: terms

The court list page (https://www.usaracquetball.com/wor/wor-court-list) states no license or reuse terms for the spreadsheet. Its footer says "All Rights Reserved" and links to the TeamUSA Terms of Use (https://www.teamusa.com/terms-of-use). Those terms:

- Section 3 bars "unauthorized spidering, scraping, or harvesting" and other automated compiling of information.
- Section 5 bars copying, reproducing, distributing, publishing or entering content "into a database" without written permission, and limits downloads to personal, non-commercial use.
- It is unclear whether the terms bind usaracquetball.com itself (they cover USOPC-operated sites; third-party sites are excluded). The site footer links to them, so I treated them as applying.

Decision: link out only. The spreadsheet was not opened and no rows were copied. Courts for this sport would need written permission from USA Racquetball or independent public sources (OSM tags, city park pages).

### Remaining `not_found` sports

Searched in grouped queries (3-6 sports per query), public web only. A grouped search can miss a sport, and "no usable directory found" means this search found none, not that none exists. No lead or link-out was added: no sport turned up a named California venue, and a link-out needs an existing venue.

| Sport(s) | Result (2026-10-10) |
|---|---|
| 1-wall Paddle, String Paddleball | No California court list. One encyclopedia page says one-wall paddleball is popular in California but names no courts. Handball/paddleball courts may already be on the map under other sports; check OSM `sport=handball` ways before adding. |
| Kadima (matkot) | No directory. Played anywhere on beaches; no California venue found. No usable directory found. |
| Frescobol (Frescoball, Frescotennis) | No directory. A San Francisco paddle seller exists (Merriment Hardware), which is a shop, not a venue. No usable directory found. |
| Road Tennis, Street Tennis, Street Racket | No California listings; results were ordinary tennis clubs. No usable directory found. |
| Racket Hockey, Ricochet, Knuckle Racket, Australian Racquetball, Wacquetball | Played on racquetball courts, which the map already covers under Racquetball. No separate directory found. |
| Crossminton (third pass 2026-11-22: see below), Speedball, Jazzminton, Goodminton, Shuttleball, Biraq, Pitton, Ball Badminton, Indiaca Tennis | No California club or directory found. Ordinary badminton clubs exist but do not list these sports. |
| Table Squash | Origin is UK (2009); no California listing. No usable directory found. |
| Tennis Baseball, Tennis Triples, Lite Tennis, Naked Tennis, Tenis criollo | No California club found. No usable directory found. |
| 360Ball, Qianball, Taiji Bailong | No US club list. 360Ball (South Africa) and Qianball (Denmark) have no US clubs in the results. No usable directory found. |
| Riftball, Skyball, Toccer, Miniten Thug, Floor Pro Mini Tennis, Pro Sunball | Mostly retail products; no clubs or courts found. No usable directory found. |
| Wall Pong, Xare, Jokari, Smolball | No result naming a California venue. Xare is a Basque pelota discipline (see Basque Pelota above). Jokari is a home game, no venue needed. No usable directory found. |
| Downside Ball Game, Eclipseball, Ketball, Pang Pong, Rapidball | Searched on their own on 2026-11-22: see the fourth pass below. |
| Loboton, Micro Pickleball, Spec Tennis, Teqis, Teqpong | **Not searched** in this pass. They have venues now, so no search needed. |

## Third pass, 2026-11-22: federation finders, per sport and region

Each of Real Tennis, Tamburello, Crossminton and Soft Tennis searched on its own, against the governing body's pages, for CA, NV, OR, WA, HI, AZ, NM, TX and the Mexico pilot. Public pages only. "No result found" means these pages showed none, not that none exists. No pin or lead was added.

| Sport | Pages read | Result (searched 2026-11-22; CA, NV, OR, WA, HI, AZ, NM, TX, MX) |
|---|---|---|
| Real Tennis | USCTA home and clubs list (uscourttennis.org/clubs, /international-courts); Tennis & Rackets Association overseas courts; Royal Tennis Court club list | No result found in any covered region. US courts listed: Boston, Newport RI, New York (2), Tuxedo Park NY, Manhasset NY (private), Philadelphia, Chicago, Lakewood NJ, Aiken SC, Vienna VA; McLean VA court closing on lease expiry. Charleston SC reported as planned (undated page). Mexico on no list. Not read: USCTA "Lost courts of America" page. |
| Tamburello | Wikipedia (edited 2026-05); web search for US and Mexico clubs | No result found. The Italian federation site (fipt.it) did not load and the international federation page was not found, so the gap is real: Italian-American clubs not checked. |
| Crossminton | ICO members list (status 2025-02-04), community finder, tournament calendar (current to Dec 2026); crossminton.us (stale, newest item Dec 2021); Speedminton USA shop | No result found in any covered region. Crossminton USA's only listing is Griffith High School, Griffith IN (outside our regions). Crossminton Mexico is a national entry (Mexico City address) with no club or event. The ICO community map could not be read (script-loaded). Speedminton USA is an online shop (Vista CA address), not a venue. |
| Soft Tennis | ISTF site and member pages | No result found. The US is a provisional ISTF member with no contact or club list; Mexico is not an ISTF member; USSTA-style sites did not resolve. Japanese-American community clubs not checked. |

Next step if the owner wants more: the ICO community map (needs a browser), Italian-American associations for Tamburello, and a Japanese-language search for Soft Tennis clubs.

## Fourth pass, 2026-11-22: sports never searched, per sport and region

Each of Downside Ball Game, Eclipseball, Ketball, Pang Pong and Rapidball searched on its own for CA, NV, OR, WA, HI, AZ, NM, TX and the Mexico pilot. Public pages only (web search, the sport's own site, Wikipedia). "No result found" means these searches showed none, not that none exists. No pin or lead was added.

| Sport | Pages read | Result (searched 2026-11-22; CA, NV, OR, WA, HI, AZ, NM, TX, MX) |
|---|---|---|
| Downside Ball Game | Wikipedia; Downside School site | No result found in any covered region. Played by pupils at one school's outdoor court ("The Ball Place"), Downside School, Somerset, England, since 1820. No US or Mexican school found. Not a venue sport for us. |
| Eclipseball | topendsports.com; retailer pages (BSN, US Games, Wolverine, Gopher) | No result found in any covered region. Created in Grant, Michigan (1985), sold as a school and gym PE set; played on a volleyball court with a net, indoors or outdoors. No league, club or event page found. Retail-only and play-anywhere. **Proposed, not added:** a `sport_play_anywhere.csv` row (`anywhere`, any volleyball court), for the owner to decide. |
| Ketball | ketball.com (about, rules) | No result found in any covered region. A pool-based game from the Netherlands (padel-like court with panels over a swimming pool); the site says its 2027 host is still to be found, and names no venue. No US or Mexico pool found. |
| Pang Pong | Wikipedia; Hitachi's own article on the sport | No result found in any covered region. Played mainly in Hitachi City, Ibaraki, Japan, within Hitachi's factory community. Outside Japan only one past event found (Harrodsburg, Kentucky, a Hitachi plant town, 2004) and a 2014 Nordic championship in Sweden. A Hitachi (now Astemo) plant exists in Queretaro, Mexico; no pang pong activity there was found. |
| Rapidball | rapidball.info; ACLO (Netherlands) page; map data (`sport_also_played.csv`) | No dedicated Rapidball club or event found in any covered region. The sport is played mainly in Mallorca, Spain, plus Denmark and the Netherlands. Its 57 map venues are **inferred**, not found: Rapidball is derived from Squash courts through `sport_also_played.csv` (owner, 2026-10-27), and the site itself says it is played on any regular squash court. Nothing removed. |

Next step if the owner wants more: Spanish-language search for Rapidball in Mallorca-linked clubs is outside our regions; Loboton, Micro Pickleball, Spec Tennis, Teqis and Teqpong need no search.

## Fifth pass, 2026-11-22: badminton-like sports, per sport and region

Each of Ball Badminton, Battlebird, Biraq, Goodminton, Jazzminton, Shuttleball and Speedball searched on its own (standard web search, public pages only), with the region names CA, NV, OR, WA, HI, AZ, NM, TX and Mexico (English and Spanish) in the query. One search per sport plus three follow-ups (Ball Badminton in Indian-American association pages, Speedball/Speedminton on Meetup, Mexico in Spanish); not one search per sport per region, so a small local group could still be missed. "No result found" means these searches showed none, not that none exists. No pin or lead was added.

| Sport | Pages read | Result (searched 2026-11-22; CA, NV, OR, WA, HI, AZ, NM, TX, MX) |
|---|---|---|
| Ball Badminton | Search results (USA Badminton member clubs, worldbadminton.com club directory, Indian-American association event pages) | No result found in any covered region. Every hit was ordinary shuttlecock badminton (clubs in CA, TX, AZ, WA, HI; Indian-American associations run badminton tournaments elsewhere in the US). The sport is South Indian; no US or Mexico club found. |
| Battlebird | Search results only | No result found: no page mentioning the sport at all. It is already in `sport_play_anywhere.csv` (anywhere), so no pin is needed. |
| Biraq | topendsports.com; search results | No result found in any covered region. Created in 1996 in Itapetininga, São Paulo, Brazil; played with a racket in each hand on a 14 x 4.5 m court. Only encyclopedia-style pages mention it; no club or league. |
| Goodminton | Search results | No result found in any covered region. One social-badminton club page (reclub.co) lists a venue called "Goodminton" among its courts; its country was not stated on the page and it is a venue name, not a sport club, so it was not used. Already in `sport_play_anywhere.csv`. |
| Jazzminton | Search results (USA Badminton pages) | No result found in any covered region. No page mentioned the sport. Already in `sport_play_anywhere.csv`. |
| Shuttleball | Search results | No result found in any covered region. Every hit was ordinary badminton leagues. |
| Speedball | Search results (worldbadminton.com, Meetup, local press) | No result found in any covered region. The name is ambiguous; no racket-sport "Speedball" club or Meetup group turned up in CA, NV, OR, WA, HI, AZ, TX. Only ordinary badminton venues came back (for example the Arizona Badminton Center in Mesa, already a badminton venue, not this sport). |

Not checked: the sports' own sites where they exist (none found for Battlebird, Jazzminton, Shuttleball), Facebook groups (not public-page readable), and Instagram.

## Sixth pass, 2026-11-22: wall and racquetball-like sports, per sport

Each of Jokari, Wall Pong, Smolball, Table Squash, Wackitball, Riftball, Ricochet, Racket Hockey and String Paddleball searched on its own (standard web search, public pages only; one to three searches per sport, plus one Spanish-language search for Mexico). Region names (CA, NV, OR, WA, HI, AZ, NM, TX, Mexico) went into the queries, but this was not one search per sport per region, so a small local group could still be missed. The search engine handled long OR queries badly, so most sports were re-run with plain queries. "No result found" means these searches showed none, not that none exists. No pin or lead was added.

Not searched, because they already have venues: 1-, 3- and 4-wall Paddleball, Wacquetball, Knuckle Racket, Australian Racquetball and every Basque Pelota discipline including Xare (all `covered` in `coverage_snapshot.md`; the last three families come from `sport_also_played.csv` and the Basque Pelota seeds).

| Sport | Pages read | Result (searched 2026-11-22; CA, NV, OR, WA, HI, AZ, NM, TX, MX) |
|---|---|---|
| Jokari | Wikipedia; donaldsauter.com and oocities.org enthusiast pages; search results | No result found in any covered region. A casual home and pavement game (ball on an elastic cord tied to a floor anchor); the pages say any paved area works and name no club, league or court. Not a venue sport. |
| Wall Pong | topendsports.com | No result found in any covered region. Created in Illinois in 2015 (a ping pong table 14 inches from a wall); the page says it can be played at home. No tournament, league or venue found. |
| Smolball | mobilesport.ch (Swiss school-sport teaching pages); wikimonde.com | No result found in any covered region. Swiss school PE game (1970s), taught in Swiss schools; no US or Mexican club, school or event found. Not read: smolball.com (not returned by search). |
| Table Squash | Wikipedia (via search); search results | No result found in any covered region. Searches returned only ordinary squash clubs (Bay Clubs, Life Time in CA, TX, AZ, WA, OR) and table tennis clubs; none mention table squash. The ITSA site was not found. |
| Wackitball | IDEMA activity guides (Belgian school-equipment seller) | No result found in any covered region. Found only as a school-equipment product from a Belgian seller; no federation, club or event page returned. wackitball.be was not reached. |
| Riftball | Retailer pages (Target, Scheels, Tractor Supply, School Health) and one product review | No result found in any covered region. A retail paddle-ball set (B3 Games) with two nets, sold for backyards and schools; no club, league or event. Added to `sport_play_anywhere.csv` (`anywhere`; owner, 2026-11-22), so no pin is needed. |
| Ricochet | Search results (racquetball and IRF pages) | No result found in any covered region: no page describing the sport as separate from racquetball. The sheet says it is played in Czech Republic, Germany and Poland. The two weak name matches already in `mart_places_to_review` stay unreviewed here. |
| Racket Hockey | topendsports.com | No result found in any covered region. Created in Missouri in 2016; no league or club page. Already in `sport_play_anywhere.csv` (any roller hockey rink or smooth pavement), so no pin is needed. |
| String Paddleball | Search results | No result found in any covered region. Only one-wall and 3-wall paddleball (NYC events, the Pacific Paddleball Association in San Diego) came back, which are other sports already on the map. Already in `sport_play_anywhere.csv`. |

Mexico (Spanish search for squash de mesa, Jokari, hockey de raqueta): only ordinary squash, racquetball and table tennis news came back; nothing for these sports.

Not checked: Facebook groups and Instagram (not readable as public pages), school PE-teacher forums, the sports' own sites that did not load, and non-English searches beyond the one Spanish query.

## Seventh pass, 2026-11-22: Beach Tennis, per region

Scope: the only sheet sport not covered by the other family passes or earlier ones is Beach Tennis (thin: 9 venues, 0 courts). Kadima/Matkot is not its own sheet row (Smashball carries it, tennis-like pass). Standard web search only, public pages, one query per region group. "None found" means these searches showed none, not that none exists. The venues already pinned stand (Santa Monica Tower 26, Manhattan Beach 7th St, Hermosa Beach 14th St, SF Bay Area four sfbeachtennis.com spots, San Diego Ocean Beach, Giammalva in Spring TX, Active Beach House in Cancún).

| Region | Result (searched 2026-11-22) |
|---|---|
| CA | Beyond the pins above, no new club, court or event found in Orange County, Long Beach, Santa Barbara, Santa Cruz, Sacramento, Tahoe, Venice or Redondo. Lead only: Beach Tennis SoCal Meetup (Long Beach, 136 members), newest listed event 2013-12-07, so likely stale. The iBeach31 open-play pages that surfaced are in Westfield, Indiana, not California. |
| NV | None found (Las Vegas, Reno, Henderson, Lake Las Vegas, Tahoe): only ordinary tennis clubs and sand volleyball. |
| OR, WA | None found (Portland, Seattle): padel, tennis, pickleball and sand volleyball only. |
| HI | None found (Oahu, Maui, Kauai, Big Island): resort tennis, pickleball and beach volleyball only. |
| AZ | None found (Phoenix, Scottsdale, Tempe, Tucson, Lake Havasu): sand volleyball courts (Scottsdale Ranch Park) exist but nothing names beach tennis. |
| NM | None found (Albuquerque, Santa Fe). |
| TX | One lead, not pinned: ATX Beach, Austin (8 sand volleyball courts, 11000 Middle Fiskville Rd) names "beach tennis" only in its waiver's activity list; its home page shows volleyball only. Houston, Dallas, Galveston, Corpus Christi: none beyond Giammalva (already pinned). |
| MX | None found beyond Active Beach House (pinned) and the 2025 Cancún Open already in `venue_leads.csv`. Spanish searches ("tenis de playa") for Tijuana, Rosarito, Ensenada, La Paz, Cabo, Mazatlán, Puerto Vallarta, Sayulita, Playa del Carmen, Tulum, Cozumel returned only conventional tennis, padel and surf. |

Not checked: Instagram and Facebook (club accounts often post sessions there), the ITF BT10 calendar for CA events (already tracked in `docs/beach_tennis_watch.md`), and in-person asks. Sheet changes proposed: none.

## Eighth pass, 2026-11-22: tennis-like and beach/novelty sports, per sport and region

Each of Street Tennis, Road Tennis, Street Racket, Tennis Baseball, Naked Tennis, Floor Pro Mini Tennis, Miniten Thug, Totem Tennis, Padel Pingpong, 360Ball, Qianball, Taiji Bailong, Frescoball/Frescobol, Smashball (Kadima/Matkot), Pro Sunball and Toccer searched on its own (standard web search, public pages only) with the region names CA, NV, OR, WA, HI, AZ, NM, TX and Mexico in the query, plus follow-ups for Miniten (US naturist clubs), Platform Tennis (APTA public-access list, the club's own page) and a Spanish-language search for Mexico. One search per sport, not one per sport per region, so a small local group could still be missed. "No result found" means these searches showed none, not that none exists. One pin was added (Platform Tennis, Arizona); no lead.

| Sport | Pages read | Result (searched 2026-11-22; CA, NV, OR, WA, HI, AZ, NM, TX, MX) |
|---|---|---|
| Street Tennis | Search results (Meetup, USTA SoCal, club leagues) | No result found for the sport. Only ordinary tennis leagues came back; Club Volley (Los Angeles) is an informal open-play community on public courts, not a named Street Tennis group, so it was not used. Already in `sport_play_anywhere.csv`. |
| Road Tennis | Search results (USTA Hawaii, club pages), Spanish-language search for Mexico | No result found in any covered region. No US or Mexico club or Korean-American association page mentioned the sport. A Korean-language search was not run. Already in `sport_play_anywhere.csv`. |
| Street Racket | Search results (Meetup topic pages) | No result found: no page mentioning the sport. Already in `sport_play_anywhere.csv`. |
| Tennis Baseball | Search results | No result found: only ordinary baseball and tennis pages. Already in `sport_play_anywhere.csv`. |
| Naked Tennis | topendsports.com; search results | No result found in any covered region. It is a net-less tennis variant invented in Italy in 2020 (despite the name, not about nudity); the only event hit was an unrelated fashion party in Switzerland. Already in `sport_play_anywhere.csv`. |
| Floor Pro Mini Tennis | Search results (VersaCourt and other floor-tile sellers) | No result found in any covered region. Only retail mini-tennis court tiles; no club or court. |
| Miniten Thug | Wikipedia; NZ Naturist Federation page; naturist-resort search | No result found in any covered region. Miniten is a naturist sport played in the UK and New Zealand (the "thug" is the bat). No US or Mexico naturist club listing mentioned a Miniten court; the AANR club directory was not read. |
| Totem Tennis | Search results | No result found: no page mentioning the sport. Nothing mapped yet in `coverage_snapshot.md`; no US or Mexico page found. |
| Padel Pingpong | padelpingpong.squarespace.com (official site and news) | No result found in any covered region. Courts reported by the sport's site: Italy (Caserta), the Netherlands (Nijkerk), Georgia (Padel Island), Denmark (Bork) and Colombia (partnership). None in the US or Mexico. Recheck the news page quarterly: it is a new padel hybrid that may reach US padel clubs. |
| 360Ball | topendsports.com; search results | No result found in any covered region. Created in South Africa; the only other hits were the unrelated 360Player club software. |
| Qianball | Wikipedia; topendsports.com; lex.dk | No result found in any covered region. Organised in China and Denmark (KFUM); no US or Mexico club. Chinese-language search not run. |
| Taiji Bailong | Same search as Qianball | No result found in any covered region. No page found for a US or Mexico group. |
| Frescoball / Frescobol | Search results, topendsports.com, Spanish-language search for Mexico | No result found in any covered region: no club or tournament; only beach volleyball, pickleball and beach tennis events. It is in `sport_play_anywhere.csv` (any beach). A Portuguese-language search for Brazilian-American beach groups was not run. |
| Smashball (Kadima / Matkot) | Wikipedia; topendsports.com; Hadassah Magazine | No result found in any covered region. Matkot is a recreational beach game in Israel (called kadima in the US); no organised club or tournament in CA, HI, TX, AZ or Mexico. In `sport_play_anywhere.csv` (any beach). |
| Pro Sunball | Search results | No result found: only an unrelated basketball event named "Sunball Classic" (South Carolina). In `sport_play_anywhere.csv`. |
| Toccer | Search results | No result found: no page mentioning the sport (TOCA Soccer is an unrelated indoor-soccer company). In `sport_play_anywhere.csv`. |
| Platform Tennis | platformtennis.org public-access list (static, by state); Sun City West Tennis Club pages (tennis.scwclubs.com/2023-platform-tennis/, /benefits-of-club-membership/); Yourvalley.net coverage | **One find, pinned: Sun City West Tennis Complex, Sun City West, AZ** (`az-sun-city-west-platform-tennis`, official, 4 courts, club members, drop-in play listed daily). The APTA list names no site in CA, NV, OR, WA, HI, NM, TX or Mexico; it lists only public-access courts, so private clubs are missing by design (it does not list Lagunitas Country Club, Ross CA, which stays an unconfirmed lead pin). Seattle stays a community lead (no deck built). |

Not checked: the sports' own sites where none was found, Facebook groups and Instagram (not readable as public pages), the AANR naturist directory, and Chinese, Korean and Portuguese-language searches.

Sheet changes proposed in the PR description, none made here.
## Ninth pass, 2026-11-22: social sources, non-English queries, AANR (zero-venue sports)

Scope: the sports recorded as "none found" in passes three to eight, re-searched through what those passes skipped: public Facebook pages, Instagram profiles and Meetup groups (web search limited to those domains, then the page header read without a login), Chinese, Korean, Japanese, Portuguese and Spanish queries, and the AANR naturist directory. Standard search only; about 25 searches, grouped by sport family (not one per sport per region), so a small local group could still be missed. "None found" means these searches showed none, not that none exists.

Limits hit: **Reddit** is blocked for the search tool (no Reddit result is possible). **Facebook and Instagram** show only the page header (name, follower count, bio) without a login; posts, events and addresses are behind a login wall, so nothing was read past the header. The **AANR club directory** is not indexed by the search tool (only its fact pages came back) and the ICO community map still needs a browser. Neither Korean nor Japanese queries surfaced a single community club page.

Added: 1 pin (reported) and 4 leads. No sheet or `all_racquet.csv` change.

| Sport | Source read | Result (searched 2026-11-22) |
|---|---|---|
| Taiji Bailong (Roliball, 柔力球) | World Journal (2026-01-05), Chinese-language search | **Found, pinned as reported:** a FlowBall USA Invitational was held at the South Coast Chinese Cultural Center, 9 Truman St, Irvine, CA (`taiji-bailong-south-coast-chinese-cultural-center`; one event, no regular practice found; coordinates approximate; lead `flowball-usa-invitational-irvine-2026`). Nothing for San Francisco, Houston, Seattle or Mexico. |
| Beach Tennis | Facebook, Instagram and Meetup pages (headers) | Hawaii Beach Tennis Association (Honolulu, Facebook, 993 followers) and Beach Tennis - Houston (Instagram, about 2,185 followers) both exist and say they offer play, but neither names a beach or address: leads `hawaii-beach-tennis-association` and `beach-tennis-houston-instagram`. Beach Tennis PlayBT California (Instagram) lists Manhattan Beach 7th St, Tue/Thu/Sat 9:00-12:00: second operator at the existing pin (lead `playbt-california-manhattan-beach`). OLA Beach Tennis, Beach Tennis Santa Monica, Beach Tennis San Diego and BT Cali Club were already mapped. Beach Tennis SoCal (Meetup, Long Beach) is confirmed stale: its newest listed event is 2013-12-07 and nothing is scheduled. ATX Beach (Austin): still only the waiver mention. Spanish query for TX, AZ, NM and MX: none found. |
| Follow-up re-read, 2026-11-23 | Public pages only (standard search, club sites); Facebook and Instagram stay login-walled | No lead could be pinned. Hawaii Beach Tennis Association, Beach Tennis Houston and PlayBT California: still no public page naming a beach or schedule (playbt.com is a parked lander). ATX Beach: home page still has no beach tennis mention. Irvine Taiji Bailong: no practice schedule found, pin stays "reported". Bonus: btcaliclub.com is readable again and lists a Dec 12 2026 Manhattan Beach tournament (added as a venue action; lead `btcc-league-3rd-edition-finals-2026` closed). The Pages deploy of the Irvine pin is live. |
| Crossminton and Speedminton | Facebook, Instagram, Meetup; Spanish query for Mexico | No result found in any covered region. Crossminton USA (Facebook, 70 followers) is a governing-body page with no club or venue; Speedminton USA (Carlsbad CA, Facebook and Instagram) is a gear seller, not a venue. No Meetup group found. |
| Real Tennis, Tamburello | Facebook, Instagram, Meetup; Italian-American club search | No result found. Only Prince's Court (McLean, VA, already known, outside our regions) and a club in Sicily. Bocce clubs came back for Italian-American groups, none with tamburello. |
| Miniten Thug | Web search of AANR, Facebook, Meetup | No result found. The AANR directory could not be read; the only AANR-linked page found (a Minnesota non-landed club) does not mention it. Glen Eden (Corona, CA) lists tennis courts but nothing says Miniten. Miniten stays a UK/NZ sport in the pages found. |
| Naked Tennis | AANR search, earlier pass | No result found: it is a net-less Italian variant, not a naturist sport (see the eighth pass), so the AANR route does not apply. |
| Soft Tennis, Tennis Baseball, Road Tennis | Japanese and Korean queries, Facebook and Meetup | No result found in any covered region. Only general tennis and Nippon Club (New York) pages returned. |
| Qianball | Chinese query | No result found. |
| Frescoball / Frescobol, Smashball (Kadima) | Portuguese query, Facebook, Instagram, Meetup | No result found for a play group in CA, TX, HI or AZ. Brand and shop pages only (Frescobol Carioca, Freskoball in San Clemente, Vero Frescobol in Florida); Kadima groups found are in New York. No pin. |
| Padel Pingpong | Facebook and Instagram | No result found: only ordinary padel clubs in Mexico. Quarterly recheck of the sport's own news page still due (next 2027-02). |
| Ricochet, Table Squash, Wall Pong, Racket Hockey, Totem Tennis, Street Racket | Facebook, Instagram, Meetup | No result found. Ricochet has a Czech Facebook page (outside our regions) and a Kansas City bar venue (outside). The other names returned only table tennis, squash and racquetball pages. |
| Ball Badminton, Biraq, Battlebird, Shuttleball, Speedball, 360Ball, Pro Sunball, Toccer, Jokari, Smolball, Wackitball, String Paddleball, Downside Ball, Eclipseball, Ketball, Pang Pong, Rapidball, Floor Pro Mini Tennis, Street Tennis | Not re-searched | No new source type applies (retail, school or non-US only in the earlier passes); results from passes three to eight stand. |

Still not covered: Reddit, the logged-in parts of Facebook and Instagram, the AANR directory and ICO map (need a browser), WeChat and Naver or Daum community groups, and school PE forums.

Sheet changes proposed in the PR description, none made here.

Remaining families not yet searched per region: none of the 2026-10-10 groups are left. Still not searched on their own: Loboton, Micro Pickleball, Spec Tennis, Teqis and Teqpong (they have venues).


## Tenth pass, 2026-11-23: OSM keyword sweep, every sport, Mexico and the US regions

`ingestion/oneoff/keyword_sport_sweep.py` queried Overpass over MX, CA, NV, OR, WA, HI, AZ, NM and TX for `sport=` values and English and Spanish `name~` / `description~` keywords of every sport in `all_racquet.csv`, then kept hits with no pin for that sport within 200 m. Tennis, table tennis and pickleball `sport=` tags were queried separately for MX only (outside the metros the extract never read them). OSM only; no page was read for any new pin.

- **Added (Mexico, tag-only, `reported`):** 95 pins: Padel 49, Table Tennis 20, Pickleball 16, Badminton 10. All say "Mapped on OpenStreetMap"; sport, use and access are not confirmed. Hotel courts say guests-only is likely.
- **Not added:** `sport=paddle` alone (ambiguous), padel tags on frontón courts, resort ping pong, street and shop names, and padel/pop-tennis/squash tags on school and park pitches in CA and AZ (OSM padel tags there are unreliable, see the padel audit). 
- **No OSM hit by `sport=`, name or description in any covered region (searched 2026-11-23):** every sport in `all_racquet.csv` not named below, including Tamburello, Soft Tennis, Crossminton, Touchtennis, Totem Tennis, Frescoball, Smashball, Jokari, Hand Tennis, Real Tennis (only a bank named "Real Tennis" in Yucatan), Table Squash, Tennis Baseball, 1/3/4-wall Paddleball and the never-searched sports above.
- **Hits too weak to pin:** Ricochet (a word), Street Tennis, Road Tennis, Skyball (artwork), Pang Pong (a name).
- **Still unswept:** MX `sport=tennis` outside the metros; the 150+ Spanish "pelota/paleta" name hits in MX (mostly not courts); the US-region candidates (squash, badminton, pickleball names in AZ, WA, TX) are listed in the PR description for a follow-up.

## Twelfth pass, 2026-11-23: US triage of the keyword sweep (CA, OR, WA, HI, AZ, TX)

- **Added (US, tag-only, `reported`):** 29 pins from OSM tags or names only (no page read): Pickleball 18, Badminton 5, Racquetball 4, Squash 2 (AZ 5, CA 10, HI 1, OR 1, TX 8, WA 5). Sport, use and access are not confirmed.
- **Not added:** all 70 `sport=padel` pitches (unreliable, same as the padel audit); `sport=squash` and `paddle_tennis` tags on park and school pitches, and badminton/pickleball tags 1 to 30 m from an existing pin (the venue exists, the sport tag is the only gap); Squash Blossom and Ricochet street names; "pelota/paleta" hits (ice-cream bars, streets, schools); Seal Beach/Newport Beach "Beach Tennis" name hits; Ladera and Sandpipers communities; the Naval Base San Diego racquetball node (military).
- **Still unswept:** NV (no hits in the candidate file); same-venue sport tags (pickleball, pop tennis, badminton on parks that have only a tennis pin, e.g. Larsen Park SF, Public Pickleball and Badminton Courts in Port Townsend); MX `sport=tennis` outside the metros.

## Eleventh pass, 2026-11-23: the "not re-searched" sports (Ball Badminton, Battlebird, Speedball, Shuttleball)

Scope: the four of the 19 sports left out of the ninth pass with the most plausible US club activity, through sources earlier passes skipped: Meetup and Facebook (web search limited to those domains), Tamil and South Asian community angles, federation pages. Standard search, 6 searches.

- **Result: none found, no pin, no lead.** Ball Badminton: only the Federation of India page and non-US Tamil groups; US badminton clubs found are ordinary badminton (UW, Caltech, San Diego, Tukwila). Battlebird: no page at all (the only near hit is Battle Court, a Miami jai alai league, outside our regions). Speedball: only Egyptian-origin and Decathlon shop pages. Shuttleball: no page.
- **Reddit is blocked** for both the search tool and the browser pane (`old.reddit.com` refused), so it stays uncovered. The other 15 sports in that row stay as the ninth pass left them (retail or non-US only).
- Next useful step, if wanted: ask the owner for any local Tamil sangam or South Asian community group that plays ball badminton, since public pages show none.

## Sixth pass, 2026-11-24: Platform Tennis, Teqpong, Teqis, Crossminton

Standard web search per sport (CA, NV, OR, WA, AZ, NM, HI), public pages only. No new court found: Platform Tennis only Sun City West AZ (already pinned); Teqball tables only in Texas results; Crossminton nothing new. No pin or lead added. Five false name matches rejected in `place_sport_overrides.csv` (2 Ricochet: a stable and a pistol range; 2 Street Tennis and 1 Road Tennis: tennis courts on streets with those names).

## Thirteenth pass, 2026-11-24: five sports never searched in the Mexico metros

Soft Tennis, Tamburello, Crossminton, Platform Tennis and Tenis criollo, searched in the border pilot metros (Tijuana with Tecate and Rosarito, Mexicali, Ensenada, Hermosillo, Nogales, San Luis Río Colorado). Federation finders first (FIBaT member list, ISTF national list, ICO entries, APTA public-access list, CATP venue finder, FMT statutes), then one or two standard web searches per sport covering the metro cluster, in English and Spanish. Not one search per metro, so a small local group could still be missed. Public pages only; no logins, no Google data. "No result found" means these searches showed none, not that none exists. No pin or lead was added.

Existing map: no Mexico pin carries any of the five sports (checked `app/data/venues.json`, region MX, 2026-11-24). The 36 Soft Tennis and 26 Tenis criollo venues are non-Mexico, and Platform Tennis stays at the one pin (`az-sun-city-west-platform-tennis`).

- **Soft Tennis:** the ISTF national list (62 federations) has no Mexico entry, and the FMT statutes do not name the sport. No club found in any metro.
- **Tamburello:** the FIBaT member list (26 national federations, no Mexico) names no club anywhere. No Italian-Mexican club or court found in Mexicali or elsewhere in the metros.
- **Crossminton:** the ICO's Mexico entry is national (Mexico City) with no club or event. Nothing found in any metro.
- **Platform Tennis:** the APTA public-access list covers US courts only. No Mexico court found in any metro. The Sun City West pin is unchanged.
- **Tenis criollo:** the CATP venue finder lists Argentina only. In Mexican Spanish "tenis" also means sneakers, and no local game under this name turned up. Nothing found in any metro.

Not searched in this pass: Baja California Sur metros (Los Cabos, La Paz and the rest) and Monterrey. Recall limit: the search tool is US-focused, and Facebook gives titles only. A local club or a Spanish-only group would be found by a phone call or a local sports paper, not by these searches.

## Fourteenth pass, 2026-11-24: the five sports in Baja California Sur and Monterrey

Scope: the Mexico metros the thirteenth pass left open. Four clusters: (A) Los Cabos, East Cape, Todos Santos; (B) La Paz, Loreto, Ciudad Insurgentes; (C) Santa Rosalía, Mulegé, San Ignacio, Guerrero Negro; (D) Monterrey. Federation finders were not repeated (FIBaT, ISTF, ICO, APTA, CATP and FMT statutes, per the thirteenth pass). Then standard web searches, one or more per sport per cluster, with Spanish follow-ups for Monterrey: 19 searches. Public pages only; no logins, no Google data.

- **Result: nothing found, no pin, no link-out, no lead.** "No result found" means these searches showed none, not that none exists.
- **Soft Tennis:** A, B and D return only tennis, padel and pickleball venues (Cabo Sports Complex, Club Baja Tennis, Pedregal Tennis Center, Somos Pádel). C is covered by the combined Loreto/Mulegé/Santa Rosalía query, with nothing. Spanish "soft tenis" and "tenis de salón" in Monterrey find nothing.
- **Tamburello:** none in A, B, C or D. The only fronton-type hits are a "Pistas de Frontenis" listing at 75 Carabineros, La Paz (Pickleball Plus, described as a pickleball venue) and a fronton at Nicolás Bravo 26, Monterrey (frontons.net). Frontenis is a Basque pelota sport, not tamburello, so both are out of scope here (see follow-ups).
- **Crossminton:** none in A, B, C or D. Mexico-wide and Monterrey searches return padel clubs only.
- **Platform Tennis:** none in A, B, C or D. Hits are padel and pickleball courts (Altapadel La Paz, Swing Padel Cabo, Power Padel and others in Monterrey).
- **Tenis criollo:** none in A, B, C or D. The Baja California Sur results are a 2020 state tennis federation restructuring story; the Monterrey results name a sneaker shop (INTER TENIS), not the sport.
- **Limits:** the search tool is US-focused, Playtomic and Pickleheads were read from search snippets (not opened), and Facebook and WhatsApp groups were not reached. A small local club is found by a phone call or a local sports paper, not by these searches.
- **Follow-ups (not added to any seed):** (1) the La Paz "Pistas de Frontenis" and the Monterrey Nicolás Bravo fronton: check them in a Basque Pelota pass using public pages only; (2) if the owner knows a local tamburello, crossminton or platform tennis group in these metros, that is the one lead this search could not produce.
