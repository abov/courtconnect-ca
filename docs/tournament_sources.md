# California tournament search, pass 1 (2026-10-12)

Standard web search per sport. Only events whose organizer page I read went into `watch_events.csv`. Everything else is a lead.

## Added to watch_events.csv
- Silicon Valley Open (squash, Oct 20-24 2026, Redwood City): official site read.
- USA Pickleball Nationals (Oct 31 - Nov 8 2026, Barnes Tennis Center, San Diego): USA Pickleball pages via search.

## Leads (found in search results only, not read at the organizer, so not added)
- Pickleball, from a third-party list (mypickleballconnect.com, fetch was rate-limited): California Pickleball Classic, Fresno, Oct 16-18; Monterey Bay Pickleball Open, Oct 23-25; Palm Desert Classic, Oct 23-25; Coachella Valley Grand Prix (Palm Desert Nov 13-15, La Quinta Nov 14-16, Palm Desert Dec 11-13); San Diego Paddle Battle, Coronado, Oct 17-18.
- PPA Malibu Showcase: resolved 2026-10-12. Official event page says Dec 14-20 at Pepperdine Ralphs-Straus Tennis Center, tickets from $25 (Nov 30 - Dec 6 appears only on third-party pages).
- USTA NorCal tri-level team event, Diamond Hills Sports Club, Oakley, Oct 16-18 (team play, little to watch).
- Paddle tennis: the Venice Beach US Open article is from Sept 2025 (Oct 18-19, 2025), so 2026 is unknown.
- USA Badminton: 2026 CA events (US Open Fullerton June, SoCal ORC Jan, Dave Freeman Open Feb, NorCal Mar/May) are all past; no fall 2026 or 2027 CA listing found. usabadminton.org/tournaments 404'd.
- Racquetball: all 2026 CA events past (Outdoor Nationals Huntington Beach July, CNRA state Pleasanton Aug); none for 2027 found.
- Table tennis: US Nationals San Jose was July 2026 (past); no later CA listing found. usatt.org/events 404'd.
- Padel: Pro Padel League Santa Monica was Aug 13-16 (past); USPA Cooley Open San Diego June (past); no 2027 CA calendar yet.
- Tennis: USTA SoCal tournament calendar not found; 2027 calendars not posted. BNP Paribas Open already in the seed.
- Pickleball MLP: only the playoff stop (Newport Beach or San Diego, Aug 13-16) in CA, past.
- Skyball: skyball.us/play lists none (past list is probably script-loaded).

## Not covered
Local club and city tournaments need the clubs' own pages or each section's calendar (USTA SoCal/NorCal, USA Badminton calendar, R2 Sports, USATT club events).

## Pass 2 (2026-10-12, governing-body pages)
Added 11 events to watch_events.csv (total now 19): USA Padel 100 Pura Padel (owner's find), 6 pickleball events from usapickleball.org's California list, 4 badminton events from usabadminton.org.
- **Padel:** uspa-tournaments.worldpadelrating.com lists only ~2 weeks ahead (15 events nationwide to Oct 25); Pura Padel is the only California one. The FIP Silver at Padel N9NE San Diego (Oct 29 - Nov 2) is the **2025** edition, not 2026. Recheck the site every couple of weeks; USA Padel's second-half calendar was not readable (padelusa.org/calendar is script-loaded).
- **Pickleball:** usapickleball.org lists 7 California sanctioned events; WPA Carlsbad Indoor (Sep 24-27) is past. Its server-rendered page and its script-formatted page differ by a day; I used the server-rendered dates (they match the Nationals banner and the Golden Ticket announcement). Non-USAP events (California Pickleball Classic Fresno Oct 16-18, Monterey Bay Open Oct 23-25, Palm Desert Classic Oct 23-25, Coronado Paddle Battle Oct 17-18) are still unverified leads.
- **Badminton:** SoCal CRC and LA International Series are marked dates_not_confirmed (tentative schedule). SoCal and NorCal 2027 ORCs not published yet (SoCal ORC is usually January in Pomona).
- **Table tennis:** no California event after the July Nationals found. OmniPong (USATT's registration site) returned HTTP 500 to scripted requests; usatt.org/events 404s. Needs a manual look at omnipong.com or the clubs (Table Tennis America Fremont, ICC Milpitas, 888 Table Tennis SF).
- **Racquetball:** none after August (R2 Sports search is script-loaded). **Squash:** only the Silicon Valley Open; US Squash junior West Coast JCT was Oct 10-12 (past). **Tennis:** USTA SoCal Open Tour page still shows the 2025 season; USTA NorCal's calendar is script-loaded (ustanorcal.com/adults/tournaments).

## Pass 3 (2026-10-12, deeper pass on script-loaded calendars)
Last run: 2026-10-12. Added 24 events (watch_events.csv now 43) and 1 lead. Repeatable steps and URLs are in `docs/tournament_refresh.md`.
- **Tennis, SoCal:** playtennis.usta.com search (36 results through Dec 6). Added 14 Level 1-6 events; skipped Level 7 round robins and WTN ladders.
- **Tennis, NorCal:** public 2026 calendar Google Sheet. Added 4 Level 4-5 events; skipped the weekly Level 6-7 events (mostly Lafayette, San Jose, Livermore, Concord, Antelope).
- **Racquetball:** R2 Sports state search found 4 events (Golden State Open, Nightmare Before Christmas, 2027 Players Championship, 2027 Outdoor Nationals). The earlier "nothing after August" was wrong because R2's page is script-loaded.
- **Table tennis:** OmniPong's 2026 list has one California event left: USATT California State Championships, Fountain Valley, Nov 21-22 (venue not listed). 2027 is not listed yet.
- **Squash:** R2 Sports has none; Club Locker still unread. Only the Silicon Valley Open.
- **Skyball:** skyball.us/play "Show past" lists 7 tournaments; the only California one is the San Diego Doubles at Chira Tennis Academy on July 9, 2026 (past; added as lead `skyball-chira-tennis-academy`). The others are in New York and Maryland. The page states "SkyBall plays on any pickleball court (44' x 20')", which backs the pickleball-court match.
- **Still unread:** Club Locker (squash), USA Padel second-half calendar, USTA NorCal Level 6-7, Meetup and city recreation events.

## Sweep B (2026-10-12): badminton 2027 and padel
- **Badminton:** no 2027 California event is published. SoCal ORC (Pomona, mid-January in 2025 and 2026) and the NorCal ORC/OLC have no 2027 prospectus yet; the 2026 U.S. Open (Fullerton, June) and the 2025 Adult Nationals (Livermore, Dec 27-30) are past. Recheck usabadminton.org for the "2027 ... ORC Prospectus Released" posts in November-December. Pomona in January is an inference, not a date.
- **Padel:** no 2027 California event. Pro Padel League Santa Monica was Aug 13-16, 2026 (past). The "USPA Master Finals, Taktika San Diego, Dec 15-17" article is from Nov 2023, so it is not a 2026 event. USA Padel is taking club applications for the 2027 Nox USA Padel Circuit, so California stops may appear on padelusa.org once chosen. Park Padel Open (South San Francisco) was Aug 2025.

## Pass 4 (2026-10-13, scoped sweep)
Last run: 2026-10-13. Added 0 events (watch_events.csv stays 43); changed 1 row.
- **Table tennis:** the OmniPong entry form (`omnipong.com/EntryForms/1078-82.pdf`, linked from the tournament list) gives the venue for the USATT California State Championships: Orange County Table Tennis Academy, Fountain Valley CA 92708 (street printed as "18071 Mountain Washington"). Events run Nov 21-22 (form header says Nov 20-22). Row updated; the map point is still the city centre, not surveyed. A plain `curl` POST to `T-tourney.asp?t=9&e=0` works without the browser pane. OmniPong also lists the USATT California Open (Burlingame, Oct 9-11), which is past.
- **PPA Malibu:** ppatour.com/events/2026/veolia-malibu-cup/ again says Dec 14-20, Pepperdine Ralphs-Straus Tennis Center; seed already correct (fixed in Sweep A). The Nov 30 - Dec 6 dates are not on the official page.
- **Squash:** US Squash's 2026-27 junior calendar has no California event after the West Coast JCT (Redwood City, Oct 10-12, past). Club Locker is still script-loaded and unread, so adult/club events remain unchecked.
- **Badminton:** usabadminton.org schedule (updated 2026-10-08, tentative) covers only Oct-Dec 2026; no 2027 ORC or any 2027 event. Recheck Nov-Dec.
- **Padel:** uspa-tournaments.worldpadelrating.com lists only USA Padel 100 Pura Padel (Sherman Oaks, Oct 17-18, already in the seed). padelusa.org/calendar shows no individual events to a text fetch.
- **Cosm Los Angeles:** cosm.com/los-angeles/events returned no events to a plain fetch (script-loaded), so nothing was verified; lead `cosm-los-angeles` stays open.

## Pass 5 (2026-10-15, scheduled refresh)
Last run: 2026-10-15. Added 2 events (watch_events.csv now 46); changed 0 rows.
- **Table tennis:** OmniPong's 2027 list (curl POST, `Year=2027`) now shows California events. Added the 2027 USATT Pacific Championship (Milpitas, Jan 8-10, junior team selection) and the 2027 USATT California State Championship (Milpitas, May 7-9), both 4-Star. Venue is inferred (entry-form PDFs give an indiacc.org contact, so likely ICC Milpitas); the PDF text could not be read (no PDF text tool here), so the map point is the city centre. Leads, not added: ICC JOOLA Spring/Summer/Autumn/Winter Opens 2027 (Milpitas, Mar 6-7, Aug 21-22, Oct 23-24, Dec 4-5), OCTTA Butterfly Winter Open (Fountain Valley, Jan 9-10, 2-Star), PongPlanet Butterfly Championships (San Carlos, Mar 20-21, 3-Star). Skipped: non-sanctioned round robins and the Long Beach TTC anniversary event.
- **No change:** USTA SoCal search (32 results to Nov 30 + La Jolla nationals; all Level 1-6 already in the seed), USTA NorCal sheet (Level 4-5 unchanged), USA Pickleball California list (same 7 events), USA Padel (only Pura Padel), USA Badminton adult schedule (updated 10-08, no 2027), R2 Sports (racquetball 4 events unchanged; squash, table tennis, padel, badminton, paddle tennis, paddleball none).
- **Not rechecked this pass** (read 2026-10-12/13): PPA schedule, Golden Tickets page, USA Badminton junior schedule, Silicon Valley Open, US Squash, skyball.us, Cosm. Club Locker still unread.
- **Failed:** usapickleball.org returns an empty page to WebFetch/curl (browser pane works); OmniPong entry-form PDFs not readable as text.
