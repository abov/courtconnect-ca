# Directories for sports with no venues yet

First pass, 2026-10-10: a general web search per sport for a California club or court directory. Public pages only (ADR 0007).
"No usable directory found" means this search found none, not that none exists. The sport-level lead is not a link-out:
`venue_actions.csv` attaches to a venue, so a directory becomes a link-out only once a venue exists.

| Sport | Result | Next step |
|---|---|---|
| Outdoor Racquetball | Directory exists: USA Racquetball's outdoor court list (https://www.usaracquetball.com/wor/wor-court-list), a spreadsheet of 600+ courts, last updated about 2022. Terms checked in the second pass (below): link out only. | Lead `outdoor-racquetball-wor-list`: do not copy rows. Ask USA Racquetball for written permission, or find courts from other public sources. |
| Soft Tennis | No California club or USSTA-style listing found. | Look for a national soft tennis association club list. |
| Crossminton | Governing body is the International Crossminton Organisation (crossminton.org); no US federation or California club found. | Check the ICO member-association page for a US contact. |
| Frontenis | No California fronton or club found. | Ask Mexican-American and Basque cultural clubs; check pelota federations. |
| Basque Pelota | No California fronton found. | As above. |
| Jai alai | No California fronton found; the sport survives mainly in Florida and the Northeast. | None planned. |
| Hand Tennis | Nothing found under this name (search returned Venice paddle tennis, already on the map). | Ask the owner what it is called locally. |
| Real Tennis | No California court found. | Check the US Court Tennis / Real Tennis association court list. |
| Tamburello | No California club found. | None planned. |
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
| Crossminton, Speedball, Jazzminton, Goodminton, Shuttleball, Biraq, Pitton, Ball Badminton, Indiaca Tennis | No California club or directory found. Ordinary badminton clubs exist but do not list these sports. |
| Table Squash | Origin is UK (2009); no California listing. No usable directory found. |
| Tennis Baseball, Tennis Triples, Lite Tennis, Naked Tennis, Tenis criollo | No California club found. No usable directory found. |
| 360Ball, Qianball, Taiji Bailong | No US club list. 360Ball (South Africa) and Qianball (Denmark) have no US clubs in the results. No usable directory found. |
| Riftball, Skyball, Toccer, Sandball, Miniten Thug, Floor Pro Mini Tennis, Pro Sunball | Mostly retail products; no clubs or courts found. No usable directory found. |
| Wall Pong, Xare, Jokari, Smolball | No result naming a California venue. Xare is a Basque pelota discipline (see Basque Pelota above). Jokari is a home game, no venue needed. No usable directory found. |
| Downside Ball Game, Eclipseball, Ketball, Loboton, Micro Pickleball, Pang Pong, Rapidball, Spec Tennis, Teqis, Teqpong | **Not searched** in this pass. Unchecked, not negative. |
