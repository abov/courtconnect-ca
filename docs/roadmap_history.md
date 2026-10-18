# Roadmap history (detail moved out of CLAUDE.md, 2026-10-17)

`CLAUDE.md` "Open, in order" keeps one or two lines per item in three buckets (doable now / after beta / parked). The long dated status text that used to sit there is kept here, keyed by the OLD item number (in brackets in CLAUDE.md where it changed). Rules and guard-rails stay in CLAUDE.md; nothing below overrides them. Add new dated detail here or in a new `docs/sessions/` note, not in CLAUDE.md.

## 1. CalNeva (ADR 0014)
Steps 2-4 done (525 NV venues live). First NV seeds done (8 venues, 1 event). Reno, Henderson, Clark County and Washoe County parks done. City of Sparks parks PARKED (site refuses all connections; owner: do not retry unless asked). Resort gyms: Life Time and North Las Vegas done 2026-10-16; Las Vegas Strip/downtown resorts, Lake Las Vegas, Club Tahoe and Reno-Tahoe/Mesquite/Laughlin checks done 2026-10-17; resort gyms CLOSED by the owner 2026-10-17: do not re-check NV resorts/casinos; Horseshoe lead resolved. Repo/Pages rename to `courtconnect` after the beta (now December), date TBD (keep a redirect stub for the old Pages URL).

## 1b. Backboards / 1-wall courts (moved up by owner 2026-10-16; was 5e)
Likely hundreds in CA + NV but OSM tags only 2 (statewide scan, 2026-10-16), so search public city park and rec pages ("tennis practice wall", "backboard", "hitting wall", "handball"), starting with LA, San Diego and the Bay Area; add to `manual_walls.csv` with `confirmation` + `evidence` + `reported_on`. Cheapest first: one metro, then propose more.
Checked so far: LA + SD city pages name none; Bay Area: Berkeley's court list names 5 practice walls (added), SF/Oakland/San Jose city pages none found; Argonaut HS added (club page). Mountain View (Cuesta, added), Palo Alto, San Rafael and Sacramento city pages checked 2026-10-17 (no more found). Orange County, Fresno and Inland Empire city pages also checked (nothing). School/college pages checked too (2 `inferred` rows added: Rinconada, Linda Vista).
Next: owner/community visit reports to confirm them (Sacramento, Berkeley campus walls need an access label in the popup).
Added 2026-10-17: give walls the same access model as courts (`public` / `restricted` / `members` / `private`, same meaning as `dim_venue` `access_type`, shown the same way in the app; walls inside a club, school, apartment complex or resort are not assumed public). `manual_walls.csv` already has `access` + `free_to_use` columns: first reconcile their values with the court vocabulary and check the export/popup treat walls like courts. (PR #212 "Walls use the venue access vocabulary" landed this; see `docs/sessions/2026-10-17-walls-access-padel-test-city-adr17.md`.) Statewide walls beyond the metros above: parked.

## 1c. Padel check (added 2026-10-17; plan `docs/padel_scan.md`)
Padel (walled glass court) and pop tennis / paddle tennis (open court, low net) are separate sports but get mixed up (OSM `sport=padel` on pop tennis courts, "paddle" in both names). Plan: audit all Padel and Pop Tennis pins, fix mix-ups with overrides, then compare each metro with padelcourtsfinder.com, padelusa.org/where-to-play and padelmapusa.com (leads only: read their terms, confirm every club on its own page) and add missing clubs to `manual_venues.csv`; finish with a dbt test so a Padel row needs a supporting signal. One metro per session, LA first.
Done 2026-10-17: audit + fixes (`docs/sessions/2026-10-17-padel-audit.md`: 26 OSM Padel tags rejected, `padel` tag now medium confidence, bogus `padel_tennis` key removed); directory sweep (CA+NV, all four directories) (`docs/sessions/2026-10-17-padel-directories-popt.md`): 25 Padel venues, 23 coming-soon/unconfirmed clubs in `venue_leads.csv`; guard-rail dbt test (#211). Next: recheck leads after openings, owner reports for Exeter / Garside / Kahler Russell Pop Tennis pins (Exeter reported + Garside rejected in #205, Kahler Russell added in #206).

## 2. Street addresses (roadmap "Fill missing street addresses")
Tiers 1-3 BUILT, `int_venue_address`, `docs/ml_plan.md`. Status 2026-10-17: of 10,273 venues 4,057 show a street (osm 102, Overture place 896, nearest Overture 2,960 and Nominatim 99, the last two labelled "Nearest address (inferred)"), 5,735 are home-like = city only by design (owner rule), 482 non-home pins are blank (439 Nominatim street-only, 43 over 150 m).
Remaining, cheapest first: (a) rerun `ingestion/reverse_geocode_blanks.py` (+ `dbt build`, `make app-data`) after every extract, for new blanks only; (b) city only for the ~480 pins with none (widen the Overture city search to ~1 km, or use the cached Nominatim city; the 2026-10-17 city fix covered cached rows); (c) DONE 2026-10-17: parent park/school `addr:*` (tier 1b, `osm_parent`, 1,193 venues; re-extract `extract_osm_parents.py` after each OSM refresh); (d) tier 4 official page + quote in `manual_venues.csv` for high-value parks/public facilities (needs phase 2 reading, `docs/ml_plan.md`); (e) DONE 2026-10-17: street-only rows show as "Near <street>" (`near_street`, `ns`, labelled inferred; trails/paths skipped). Home-like pins are never filled with a street (owner 2026-10-16); OSM-tagged ones are kept.

## 3. Visual polish
Option A PRs 1-4 live, `docs/ux_polish.md`: PAUSED until beta findings (December). Then optional B parts: PR 5 popup grouping + status band, PR 6 sport glyph pins. Owner to eyeball live at 375/320px + dark. Browser pane tips: it does serve localhost (`preview_start courtconnect-map`); screenshots are blank until a second capture, and a cache-busting `?v=N` is needed after edits; opening-soon rings checked at 375 px + dark on 2026-10-17.

## 4. Accuracy
Band counts done 2026-10-14j. Review queue from public pages PARKED by owner 2026-10-17 (116 left after batch 11 + ADR 0016): batches 10-11 settled only 14 and 8 rows, 50 rows have no website and 33 a dead one, so the rest needs another source (phase 2 reader or community reports); the last pass over the ~35 live-site rows is NOT planned (`docs/review_priority.csv` stays for reference). Match gold set: plan in `docs/gold_set_plan.md`, first slice built 2026-10-17 (40 labels, `make eval-match`: 17 missed merges, no wrong merges; next slice in the plan).

## 5b. Gym chain + public-facility courts, CA + NV (plans `docs/gym_chain_scan.md`, `docs/public_facility_scan.md`)
LA Fitness, Bay Club, 24 Hour Fitness, ClubSport Aliso Viejo, Henderson + Las Vegas + Hawthorne public facilities done; Life Time/Equinox/Sports Club LA list no racquetball. The 4 leads are closed (2026-10-15). YMCA pass done (East Bay, SF, Silicon Valley, San Diego, Southern Nevada). All planned YMCA associations done (incl. Long Beach, Glendale, Santa Monica, Foothills, Whittier, 2026-10-16); first university + Navy pass done (UCLA, Berkeley, UCSB, UCI, UCSD, Stanford, UNLV, UNR, Balboa). Next (optional): other UC/CSU campuses, more military MWR, more city pages by region.

## 5c. Public facilities (city/county/park rec centers, all racket sports, CA + NV)
Plan in `docs/public_facility_scan.md`, pilot Hawthorne Sports Center (lead `hawthorne-sports-center`). Branch `public-facility-scan`. San Diego County pass done 2026-10-16 (16 cities checked); next: City of San Diego rec centers (`pb-sandiego-rec-centers`), Sacramento area, Orange County, Inland Empire.

## 5d. ML (plan `docs/ml_plan.md`)
Phase 1 review-queue ranker BUILT (`make rank-review` -> `docs/review_priority.csv`; use it to pick review batches). After beta (December): phase 2 LLM reads public pages (ADR first; ADR 0017 is the proposed LLM page reader), phase 3 pilot detecting courts in NAIP aerial photos (Hawthorne, then one LV zip; new courts go to OSM).

## 6. Coverage
`*-access` leads (14 of 62 resolved 2026-10-16, 48 unresolved with reasons in the lead notes; rest need the club or a browser-pane read), club-named venues pass 2 (first slice of 28 worked; ~12 of the ranker's club-named rows have dead domains), beach tennis court locations from clubs, statewide walls (parked), NorCal Equinox, OSM fix list (optional).

## 7. Rechecks and watch-event split
Recheck: Club Locker (squash), Cosm events, badminton 2027 ORCs (Nov-Dec). After beta findings (December): split watch events into on-site vs virtual (screenings such as Cosm showing tennis): new `watch_format` value `screening` (column exists; add accepted_values test), app popup label/filter "On-site" / "Screening (shown on screen, not played here)", then add Cosm events as screenings. Plan: `~/.claude/plans/i-wonder-if-we-dazzling-frog.md`. (Planned 2026-10-15m, start was ~2026-11-02; now gated on beta.)

## 7b. Sport discovery and tennis visibility (after beta; rank with beta findings, ADR 0015)
Sport discovery ("Try something new" card per sport, lesser-known sports given room, try-it events) and tennis visibility (own pin look, never hidden in a pickleball pin, shared courts show both sports, picker not ordered by count; plan with `docs/ux_polish.md` PR 6).

## 7b2. All sheet sports in the dropdown (after beta; plan `docs/sport_discovery_plan.md`)
Show all 76 sheet sports in the dropdown (55 with no venue are hidden today: show greyed out "no places yet" + empty-state card; blurb/wiki columns go in the Google Sheet; no popularity labels) and an "About <sport>" card (blurb, quick facts from the sheet, wiki/official link); then search real venues for unmapped sports, one family per session.

## 7c. Social phase A (after beta)
"Find people to play with" from existing groups (open play, clinics, ladders, Meetup/WhatsApp/Partiful; public pages, `verified_on` + evidence). Phase B (own accounts/matching) only with its own ADR and if beta shows demand. Competitor scan + why not Plei's hosted-games model: `docs/competitor_scan.md`.
Todo (2026-10-17): consider integrating with, or building a format like, connectplayers.ca and other player-connecting platforms. Scan first (public pages only), then choose link-out vs. own format; own accounts/matching stays phase B (own ADR).

## 7d. Community reports step 3 (LATER, parked 2026-10-16)
Report without GitHub (Google Form -> sheet -> `make sync-reports`). Owner creates the form first (setup in `docs/community_reports_plan.md`). Steps 1-2 live (#149, #152).

## 7e. ITF events (partly done 2026-10-17)
ITF W35 Redding, W35 Bakersfield + M25 DragonRidge Open (Henderson) added; no other upcoming ITF CA/NV events and no ITF Beach Tennis CA/NV event found for 2026 (note `docs/sessions/2026-10-17-itf-events.md`). Next: ITF 2027 calendars when published (~Dec; none yet 2026-10-17). ITF pages block scripts: read singly in the browser pane; facts only (name, dates, venue, link), no scraping.

## 7f. Cost tier per venue and hitting wall (after beta; added 2026-10-17; rank with beta findings)
"Free / $ / $$ / $$$" (cost to book or use). Phase 1 is rule-based from what the place is listed with (public park or wall = Free; city rec center or school = $; paid public or pay-to-play = $$; private club, resort or apartment = $$$ or "members/residents only", with guest or day-pass noted if public pages say so). New `price_tier` + `price_basis` (`confirmed` from a public page, else `inferred`) + `evidence` in a seed (e.g. `venue_price.csv`). Honesty: label inferred tiers as estimates, never a quote; CourtConnect takes no bookings or payments. ADR first (tier definitions; members-only gets no tier), then a gold set of ~50 confirmed prices to test the rules; ML (`docs/ml_plan.md`) only if rules prove too coarse. Needs the shared access model from 1b so walls and courts behave the same. Public pages only (ADR 0007).

## 8. MCP server (LATER, after beta)
Optional read-only CourtConnect MCP server over `venues.json` (details in docs/status_history.md, TODO 2026-10-14; ADR first).

## 9. Beta round (TIME-BOXED; docs/feedback_round.md; moved to December by owner 2026-10-17, exact dates TBD)
Send the round, collect replies, record findings, then fill case study + docs/feedback_findings.md (RICE). Owner: exclude own IP in GoatCounter. Items marked "after beta" wait for these findings.

## 10. Owner-confirm items (TIME-BOXED, small)
Owner to confirm Basque Pelota (Chino trinquet, South SF center) by 2026-11-16; owner review of UX live.
