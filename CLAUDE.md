# CourtConnect CalNeva

Racket-sport venue finder for California + Nevada ("CalNeva", ADR 0014): Python ingestion -> dbt (DuckDB dev/CI, Snowflake prod) -> static MapLibre map in `app/`.
README.md has the full story; read it only if you need background. Mission (ADR 0015): help people find every place to play or watch racket sports in CA + NV, discover sports beyond pickleball (tennis stays visible), and get together to play.
Decisions are in `docs/decisions/` (ADRs 0001-0015, all accepted; one file each, read only the one you need).

## Commands (run from Git Bash on Windows)
- `make build`      dbt seeds + models + tests (the main check; run after any change to `transform/`)
- `make app-data`   export `app/data/venues.json` for the map (commit it after any seed change; CI runs `ci/check_export_fresh.py`); `make app` serves it at localhost:8765
- `make extract` / `make load`   refresh raw data (extract takes ~15 min; don't run unless asked)
- `make check-links` / `make check-websites`   verify link-outs / flag dead venue sites
- `make issues`     read-only check of open GitHub issues (missing info, already in seeds, duplicates, waiting); runbook step 2b
- `make report`     regenerate `docs/coverage_snapshot.md`
- `make snowflake-build`   RETIRED (2026-10-14): do not run; DuckDB is the only warehouse

## Rules
- NEVER read, print or commit `.env` (credentials). `.env.example` shows the keys.
- Never put the owner's email or any personal contact in request headers, query strings or forms sent to outside services (geocoders, APIs, scrapers). Identify requests with the project contact only: `User-Agent: courtconnect-ca/0.1 (+https://github.com/abov/courtconnect-ca)`.
- Never hand-edit `transform/seeds/all_racquet.csv` or Snowflake `RAW.ALL_RACQUET`: the Google Sheet is the source, `make sync-sports` overwrites them.
  The sheet must stay in sync with the project: run `make sync-sports` at every project sync (twice a month, `docs/monthly_refresh.md` step 2) and carry renames/new sports through seeds, scripts and the app.
- Data edits go in seeds, then `make build`:
  - `manual_venues.csv` (venues no dataset knows), `venue_actions.csv` (link-outs; keep `verified_on` + `evidence`),
  - `watch_events.csv` (https links only), `place_sport_overrides.csv` (confirm/reject uncertain matches), `sport_aliases.csv`, `closed_places.csv` (Overture places that no longer exist but are still listed open; `place_id` + `evidence` + `verified_on`).
- Models must run unchanged on DuckDB and Snowflake: use `adapter.dispatch` macros, no engine-specific SQL.
- Honesty over polish: label inferred data as inferred, never present guesses as confirmed. CourtConnect links out; it takes no bookings or payments.
- NEVER use the owner's logins (Playtomic, PlayByPoint, Padel Up, etc.) or read logged-in pages; use public pages and what the owner reports (ADR 0007).
- Don't use Google Places data (terms forbid storing it); Overture + OSM only (ADR 0005).
- Ignore generated/bulky paths when searching: `transform/target`, `transform/logs`, `courtconnect.duckdb`, `app/data/venues.json`.

## Keeping usage low
- Don't take browser screenshots unless I ask. Read pages as text (`get_page_text` / `read_page`) instead.
- In auto mode (or whenever I haven't picked an approach), always choose the cheapest path that does the job, and say in one line what it is:
  - Do it directly with Grep/Read/Edit; don't spawn subagents, run deep-research, or use extended web search unless I ask.
  - Run the narrowest check (`dbt build --select <changed models>`, one test) before the full build; run the full build once at the end.
  - Never start `make extract`/`make load`/`snowflake-build`, or loops/scheduled tasks, without asking.
  - Prefer one batched tool call over many; stop once the task is done instead of extra "nice to have" work.
  - If a task looks expensive (many pages to research, big refactor), propose the cheaper scoped version first and wait for my OK.
- Read only the lines you need from big files; don't dump whole CSVs, logs or `venues.json`.
- One task per session. Keep sessions small: when context passes ~200-300k tokens, write the session note and tell me to start a fresh session.
- At the end of a session, write a 2-3 line note in a NEW file `docs/sessions/YYYY-MM-DD-<topic>.md` (what changed, what is next). Never edit another session's note or add lines to a shared log: that is what caused merge conflicts. Update "Open, in order" below only when priorities change.
- Use a lighter model for simple edits; save the biggest for hard problems.

## Where things are
- `ingestion/`   Python extract/load/export scripts
- `transform/`   dbt project (models, seeds, macros, tests)
- `app/`         static map page
- `ci/fixtures`  small sample data for CI

## Current status
Session notes: one file per session in `docs/sessions/` (read only the newest 1-2 when picking up). Older log: `docs/status_history.md`. Plan: `~/.claude/plans/create-a-revised-plan-temporal-yao.md`.

**Working practices**
- Build: `.venv/Scripts/dbt build --project-dir transform --profiles-dir transform` (no `make` in Git Bash). A worktree needs a copy of `courtconnect.duckdb`.
- Seed column changes need `--full-refresh`. **Snowflake is retired as of 2026-10-14 (access may be gone): DuckDB only, never build or sync Snowflake.** Its code stays until an ADR removes it.
- Commit `app/data/venues.json` after `make app-data`. Re-run `pages.yml` after merging any app/export change; check the latest run (another session's run cancels yours). Confirm a PR is MERGED before calling it shipped.
- Dirty main checkout: `git worktree add ../x -b branch origin/main`, use the main `.venv`, copy `.env` only for the Snowflake build, then delete it.

**Done (summary):** CA map with link-outs, confirmation levels, leads, suggest-a-change form -> PR workflow (ADR 0008), social/WhatsApp/Meetup/Partiful link-outs (ADR 0009/0010/0012), OSM edit link (ADR 0011), GoatCounter analytics (ADR 0013, site `courts`), logo C, UX Option A PRs 1-3, 43 tournament events, 265 hitting walls (LA/SD/Bay OSM + 2 owner), private-club passes 1-2 (partial), `ref_sport_fit`, `mart_sport_evidence`, `mart_venue_confidence` rules_v2 (not exported), `make quality` scorecard incl. 35-day freshness SLA, monthly runbook, ADR 0014 CalNeva step 1 (`REGIONS` in `ingestion/overpass.py`, `ci/check_regions.py`).

**Open, in order**
1. CalNeva (ADR 0014): steps 2-4 done (525 NV venues live). First NV seeds done (8 venues, 1 event). Reno, Henderson, Clark County and Washoe County parks done. City of Sparks parks PARKED (site refuses all connections; owner: do not retry unless asked). Next: resort gyms (Life Time and North Las Vegas done 2026-10-16); repo/Pages rename to `courtconnect` after the beta, target 2026-12-01, TBD (keep a redirect stub for the old Pages URL).
1b. Backboards / 1-wall courts (moved up by owner 2026-10-16; was 5e): likely hundreds in CA + NV but OSM tags only 2 (statewide scan, 2026-10-16), so search public city park and rec pages ("tennis practice wall", "backboard", "hitting wall", "handball"), starting with LA, San Diego and the Bay Area; add to `manual_walls.csv` with `confirmation` + `evidence` + `reported_on`. Cheapest first: one metro, then propose more. LA + SD city pages name none; Bay Area: Berkeley's court list names 5 practice walls (added), SF/Oakland/San Jose city pages none found; Argonaut HS added (club page). Next: other city court lists (Palo Alto, Mountain View, Marin, Sacramento) or owner/community reports. Also (added 2026-10-17): give walls the same access model as courts (`public` / `restricted` / `members` / `private`, same meaning as `dim_venue` `access_type`, shown the same way in the app; walls inside a club, school, apartment complex or resort are not assumed public). `manual_walls.csv` already has `access` + `free_to_use` columns: first reconcile their values with the court vocabulary and check the export/popup treat walls like courts.
2. Beta round (docs/feedback_round.md): replies due 10-28, findings 10-29..11-01, then fill case study + docs/feedback_findings.md (RICE). Owner: exclude own IP in GoatCounter.
3. Visual polish (Option A PRs 1-4 live, `docs/ux_polish.md`): PAUSED until beta findings (10-29..11-01). Then optional B parts: PR 5 popup grouping + status band, PR 6 sport glyph pins. Owner to eyeball live at 375/320px + dark (never rendered by me: browser pane refuses localhost).
4. Accuracy: (band counts done 10-14j) Overture/OSM match gold set, clear the review queue from public pages (201 left after batch 5; pick batches from `docs/review_priority.csv`).
5. Small: owner to confirm Basque Pelota (Chino trinquet, South SF center) by 2026-11-16; owner review of UX live.
5b. Gym chain + public-facility courts, CA + NV (plans `docs/gym_chain_scan.md`, `docs/public_facility_scan.md`): LA Fitness, Bay Club, 24 Hour Fitness, ClubSport Aliso Viejo, Henderson + Las Vegas + Hawthorne public facilities done; Life Time/Equinox/Sports Club LA list no racquetball. The 4 leads are closed (2026-10-15). YMCA pass done (East Bay, SF, Silicon Valley, San Diego, Southern Nevada). All planned YMCA associations done (incl. Long Beach, Glendale, Santa Monica, Foothills, Whittier, 2026-10-16); first university + Navy pass done (UCLA, Berkeley, UCSB, UCI, UCSD, Stanford, UNLV, UNR, Balboa). Next (optional): other UC/CSU campuses, more military MWR, more city pages by region.
5c. Public facilities (city/county/park rec centers, all racket sports, CA + NV): plan in `docs/public_facility_scan.md`, pilot Hawthorne Sports Center (lead `hawthorne-sports-center`). Branch `public-facility-scan`. San Diego County pass done 2026-10-16 (16 cities checked); next: City of San Diego rec centers (`pb-sandiego-rec-centers`), Sacramento area, Orange County, Inland Empire.
5d. ML, plan in `docs/ml_plan.md`: phase 1 review-queue ranker BUILT (`make rank-review` -> `docs/review_priority.csv`; use it to pick review batches); after beta (from 11-02): phase 2 LLM reads public pages (ADR first), phase 3 pilot detecting courts in NAIP aerial photos (Hawthorne, then one LV zip; new courts go to OSM).
6. Coverage: `*-access` leads (14 of 62 resolved 2026-10-16, 48 unresolved with reasons in the lead notes; rest need the club or a browser-pane read), club-named venues pass 2 (first slice of 28 worked; ~12 of the ranker's club-named rows have dead domains), beach tennis court locations from clubs, statewide walls (parked), NorCal Equinox, OSM fix list (optional).
7. Recheck: Club Locker (squash), Cosm events, badminton 2027 ORCs (Nov-Dec). From ~2026-11-02: split watch events into on-site vs virtual (screenings such as Cosm showing tennis): new `watch_format` value `screening` (column exists; add accepted_values test), app popup label/filter "On-site" / "Screening (shown on screen, not played here)", then add Cosm events as screenings. Plan: `~/.claude/plans/i-wonder-if-we-dazzling-frog.md`.
7b. After beta (rank with beta findings, ADR 0015): sport discovery ("Try something new" card per sport, lesser-known sports given room, try-it events) and tennis visibility (own pin look, never hidden in a pickleball pin, shared courts show both sports, picker not ordered by count; plan with `docs/ux_polish.md` PR 6).
7b2. After beta (plan `docs/sport_discovery_plan.md`): show all 76 sheet sports in the dropdown (55 with no venue are hidden today: show greyed out "no places yet" + empty-state card; blurb/wiki columns go in the Google Sheet; no popularity labels) and an "About <sport>" card (blurb, quick facts from the sheet, wiki/official link); then search real venues for unmapped sports, one family per session.
7c. After beta: social phase A, "Find people to play with" from existing groups (open play, clinics, ladders, Meetup/WhatsApp/Partiful; public pages, `verified_on` + evidence). Phase B (own accounts/matching) only with its own ADR and if beta shows demand. Competitor scan + why not Plei's hosted-games model: `docs/competitor_scan.md`.
7d. LATER (parked 2026-10-16): community reports step 3, report without GitHub (Google Form -> sheet -> `make sync-reports`). Owner creates the form first (setup in `docs/community_reports_plan.md`). Steps 1-2 live (#149, #152).
7e. LATER (added 2026-10-16): more tennis + beach tennis watch events and possible venues in CA + NV from the ITF site (https://www.itftennis.com/en/, tour/tournament calendars, incl. ITF Beach Tennis). Public pages only: add events to `watch_events.csv` (https links, `verified_on` + evidence), venues the events name to `manual_venues.csv` if no dataset has them. Check the ITF terms before copying anything beyond facts (name, dates, venue, link). Cheapest first: one calendar search filtered to CA + NV, then propose more.
7f. After beta (added 2026-10-17; rank with beta findings): cost tier per venue and hitting wall, "Free / $ / $$ / $$$" (cost to book or use). Phase 1 is rule-based from what the place is listed with (public park or wall = Free; city rec center or school = $; paid public or pay-to-play = $$; private club, resort or apartment = $$$ or "members/residents only", with guest or day-pass noted if public pages say so). New `price_tier` + `price_basis` (`confirmed` from a public page, else `inferred`) + `evidence` in a seed (e.g. `venue_price.csv`). Honesty: label inferred tiers as estimates, never a quote; CourtConnect takes no bookings or payments. ADR first (tier definitions; members-only gets no tier), then a gold set of ~50 confirmed prices to test the rules; ML (`docs/ml_plan.md`) only if rules prove too coarse. Needs the shared access model from 1b so walls and courts behave the same. Public pages only (ADR 0007).
8. LATER (after beta): optional read-only CourtConnect MCP server over `venues.json` (details in docs/status_history.md, TODO 2026-10-14; ADR first).
