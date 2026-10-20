# Tournament refresh runbook (run every ~2 weeks)

Monthly refresh of everything else (extracts, link checks, 35-day freshness SLA): see `docs/monthly_refresh.md`.

Goal: keep `transform/seeds/watch_events.csv` current for California. Only add events whose dates and venue you read at the organizer or governing body. Label anything inferred (see the `location_precision`, `date_status` and `source_note` columns). CourtConnect links out; no bookings or payments. Never use the owner's logins.

Cost rules: no subagents, no screenshots, no extended web search. Read pages as text. One batched call beats many.

## Steps
1. Start from fresh `main` on a new branch `claude/tournaments-YYYY-MM-DD`. Read the last 30 lines of `docs/tournament_sources.md` for what was already covered and the "Last run" date.
2. For each source below, collect California events dated today or later and not already in `watch_events.csv` (match on name + start_date). Add rows with the same columns as existing rows (`event_key` is a lowercase slug ending in the year). Use `level` pro / amateur / college / junior; `watch_format` `in_person_unconfirmed` unless the source states ticketing; `date_status` `dates_not_confirmed` if the source says tentative; `verified_on` = today.
3. Update changed dates of existing rows (a source disagreeing with the seed is flagged in `source_note`, not silently overwritten when the seed came from the official page).
4. Run `.venv/Scripts/dbt build --select stg_watch_events watch_events mart_watch_events --project-dir transform --profiles-dir transform` and `python ci/check_seed_evidence.py`, then the full `dbt build` once.
5. Append a "Pass N (date)" section to `docs/tournament_sources.md` (added, changed, sources that failed) and set "Last run: date" at the top of that section. Update CLAUDE.md "Current status" with 2 lines.
6. Commit, push, open a PR. Do not merge. Do not run `make extract`, `make load`, `snowflake-build`, or `pages.yml`.

## Sources (what worked on 2026-10-12)
| Sport | Source | How |
|---|---|---|
| Tennis, SoCal | https://playtennis.usta.com/tournaments?panel=section&level-category=adult&location=San%20Diego,%2092114&organisation-group=6f20620d-90b5-4a74-bf20-18b0cdd90f98 | Browser pane. Click the SEARCH button with JS, wait ~6 s, read `document.body.innerText` (results are listed ~2 months ahead). Keep Level 1-5 and prize-money Level 6 events; skip Level 7 round robins and WTN ladders. |
| Tennis, NorCal | The Google Sheet linked from https://www.ustanorcal.com/adults/tournaments/ ("2026 TOURNAMENT CALENDAR"; find the current-year link on the page) | `curl -L "<sheet>/export?format=csv"`. Keep Level 4-5 and Open. The sheet's year changes: look for the new link in January. |
| Pickleball | https://usapickleball.org/tournaments/?filter=true&tournament_state=California | Browser pane or WebFetch. The script-formatted page can show dates one day early; the server-rendered page and the event/news page are right. Also check https://usapickleball.org/goldenticket/ and the PPA schedule https://www.ppatour.com/schedule/ (the seed's PPA rows came from there). |
| Padel | https://uspa-tournaments.worldpadelrating.com/tournaments?country=US | Browser pane `get_page_text`; lists only ~2 weeks ahead. Keep rows with a California city. **Primary:** https://padelusa.org/calendar/ in the browser pane (works; 70 events, 4 pages of 20: click the `.pagination-item` numbers, wait ~2.5 s each, parse `innerText` split on `START DATE`; match rows with blank state by club name). Registration links appear only once an event has a page; calendar-only rows get `dates_not_confirmed`. See Pass 8 in `tournament_sources.md`. |
| Badminton | https://usabadminton.org/athletes/adults/adult-tournament-schedule/ and the junior schedule `.../athletes/juniors/junior-tournament-schedule/` | WebFetch. The schedule has no states; California clubs: Bintang (Fremont), Bay Badminton Center (Milpitas), Elite Badminton Center (Union City), San Gabriel Valley BC (El Monte), Arena (Pomona), San Diego BC, Titan Gym (Fullerton). Prospectus pages state the city. |
| Racquetball, squash, table tennis, padel, paddle tennis (secondary) | https://www.r2sports.com/r2sports-event-search.asp?searchNow=YES | Browser pane. On the search page, in JS: take the form that has `stateID`, set `countryID` to United States (the page reloads once), then `fetch(form.action,{method:'POST',body:new URLSearchParams(formData)})` with `stateID=6` (California) and `sportID` Racquetball 1, Squash 4, Table Tennis 22, Padel 1122, Badminton 20, Paddle Tennis 55, Paddleball 57, Pickleball 64. Parse rows with a date. |
| Table tennis | https://www.omnipong.com/t-tourney.asp | Browser pane on that page, then JS `fetch('https://www.omnipong.com/T-tourney.asp?t=9&e=0',{method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:'Year=2026&Keyword=&=Search'})` (use the current year; `Year=Current` returns nothing). Keep rows whose city ends `, CA`. Do not store contact names or phones. |
| Squash | https://siliconvalleyopen.com/ and https://ussquash.org (junior calendar) | Club Locker is script-loaded and unread; the Silicon Valley Open (Redwood City) is the only California squash event found so far. |
| Skyball | https://skyball.us/play | Browser pane, click "Show past"; the plain fetch shows "No tournaments currently scheduled". |
| Paddle tennis | Search for the Venice Beach US Open of Paddle Tennis for this year; APTA platform tennis is not a California scene. | Standard web search. |
| Dome screenings | https://www.cosm.com/los-angeles/events and https://www.cosm.com/categories/sports | Browser pane, JS: wait ~3s, then regex the page text for tennis/pickleball/padel/badminton/squash/Wimbledon/US Open. Cosm Los Angeles (Inglewood) is the only California venue. None found 2026-10-12; if one appears, add a `dome_screening` row. |
| Pro (all sports) | PPA, Premier Padel, PSA squash, BNP Paribas Open, BWF/US Open badminton | Organizer sites. |
| Tennis + beach tennis, ITF pro tour (CA + NV) | itftennis.com tournament pages (ITF World Tennis Tour M15/M25/W15-W100, ITF Beach Tennis) and the host club's own event page | Added 2026-10-17. The ITF site shows a bot check to scripts (curl, WebFetch): do not work around it. Find events with a web search ("W35 <city> CA <year>", "M25 Las Vegas NV <year>") or the Wikipedia quarterly pages "<year> ITF Women's/Men's World Tennis Tour (October-December)", then open each tournament's `/fact-sheet/` page one at a time in the browser pane (`get_page_text`) for name, dates, venue name and address. Confirm dates on the host club's event page when there is one. Copy facts only (name, dates, venue, link; no descriptions, logos or images; no scraping or bulk reads: the ITF terms bar data mining). Reuse the venue's existing pin from `venues.json`; add to `manual_venues.csv` only if no dataset has it. **Dec 2026 check:** look for the 2027 ITF World Tennis Tour calendar for CA + NV (ITF entry is via the USTA Pro Circuit, so also read the USTA 2027 Pro Circuit schedule) and the 2027 ITF Beach Tennis calendar (none was published on 2026-10-17; no CA/NV beach tennis event found for 2026). Also skim ITF Masters, wheelchair and junior CA/NV events (none found 2026-10-17). |

## Nevada (added 2026-10-15)
Same governing-body steps, filtered to Nevada, plus: https://www.bounce.game/city/las-vegas-nevada-us and `/city/reno-nevada-us` (WebFetch; lists amateur pickleball with the venue on each event page; third-party, so label unconfirmed), OmniPong with `, NV` in the city (browser pane, same fetch as table tennis), https://www.thesphere.com/events (flag any racket sport or screening). R2 Sports: do NOT loop state/sport searches; one request per sport at most, because it IP-blocks for repeated reCAPTCHA pages. USTA Intermountain needs the section id in the playtennis.usta.com URL (find it by picking Intermountain once in the Section menu).

## Known gaps
Local club-run events that are not on a governing-body calendar (Meetup groups, city recreation departments, club ladders) are not covered. Lead rows belong in `venue_leads.csv` or `docs/tournament_sources.md`, not `watch_events.csv`.

## Social links (ADR 0009)
Rows in venue_actions.csv with action_type=social: check each link still loads (make check-links) and that the club's own site still links to the account; remove dead ones. Add new handles only when the club's own site shows them.

## WhatsApp invite links (ADR 0010)
Rows with provider whatsapp: check each link still loads and the club's own site still shows it; remove dead or revoked invites.

## Meetup and Partiful links (ADR 0012)
Rows with provider meetup or partiful: check each link still loads and the club's own site still links to it; remove dead ones. Add new ones only from a club's own site or a suggest-a-change submission. Never search behind a login, never copy descriptions or attendee lists.

## Beach tennis
Recheck: olabeachtennis.com (open play times at Tower 26, leagues), sfbeachtennis.com (park locations, training tour 18 Oct, SFBT League page), and the San Diego beach tennis social links (leads `beach-tennis-mission-beach-tower-22`, `sfbt-*`). Promote a lead to `manual_venues` only once the club gives a court location.
