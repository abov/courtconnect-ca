# CourtConnect CalNeva

**Find where to play, who to play with, and where to watch, for every racket sport in California and Nevada** ("CalNeva", [ADR 0014](docs/decisions/0014-calneva-scope.md)).

**[Open the live map](https://abov.github.io/courtconnect-ca/)**

| Play | Watch |
|---|---|
| ![Pickleball venues across LA and Orange County, clustered, with filters](docs/screenshots/map-play.png) | ![Upcoming pro events across California, with dates and organizer links](docs/screenshots/map-watch.png) |

*CourtConnect is a discovery tool for all racket sports: it finds where to play or watch, then sends you to the venue's or organizer's own site. It sells no tickets and takes no bookings or payments.*

Tennis, padel, pickleball and squash and dozens of lesser-known and up-and-coming racket sports are booming, but information about *where to play* is scattered and messy. Court finders each cover one sport, or only places you can book. This project is one free map of all of them, from free park courts and hitting walls to private clubs. It collects the data, cleans it, checks it, and says honestly how complete it is.

## Who it is for
| Audience | They ask | What they get |
|---|---|---|
| **Player** | "Where can I play, and with whom?" | The map and filters, a Play / Watch / Social view, directions, link-outs to open play, leagues and lessons |
| **Curious player** | "Is there any padel, squash or pop tennis near me?" | All 81 sports on the master sheet in one picker, each with an About card; sports with no place yet say so instead of faking pins |
| **Spectator** | "What can I watch?" | 80 dated pro and amateur events with the organizer's own link |
| **Club or organizer** | "Are we listed, and is it right?" | A free pin, an honest label, and a no-account path to fix or add a listing or an event (in the About dialog) |
| **Researcher or builder** | "Can I use the data?" | One public JSON file, a data dictionary and an `llms.txt` ([below](#for-builders-and-ai-tools)) |

Not offered, on purpose: bookings, payments, accounts, rankings or paid placement. A label changes only with public evidence ([value proposition](docs/value_proposition.md), [product brief](docs/product_brief.md)).

## What it does
Live numbers (2026-10-23): **10,277 venues** (CA 9,732, NV 545), 4,536 with a name, 1,650 confirmed, 4,291 with a street address; **39 of 81 sports** have at least one venue; 80 watch events, 21 recurring social series, 923 hitting walls (448 pins), 276 link-outs, 10 player-finding apps. Counts by sport: [`docs/coverage_snapshot.md`](docs/coverage_snapshot.md).

- **Venue map** from two open sources (OpenStreetMap and Overture Maps) plus hand-curated entries, with courts grouped into venues by proximity. Filter by sport, surface, indoor/outdoor, access, or search by name, city or ZIP. Filters live in the URL, so any view is shareable.
- **Honest about confidence:** pins show how much to trust each name and sport (confirmed, business listing, inferred). A **How complete is this data?** panel lists every sport, including those with no data yet.
- **Play / Watch / Social:** Play finds courts; Watch lists upcoming pro and amateur events; Social shows recurring open-play series and player-matching apps (social phase A, [ADR 0015](docs/decisions/0015-mission-and-social-phase.md)). A separate **hitting-wall** layer serves solo practice.
- **Link-outs** to a venue's own pages for open play, lessons and leagues, each with a `verified_on` date and an evidence note.
- **Popup built for decisions:** a status band (confirmed / listed business / inferred), sports and courts grouped, rules and access as written on the venue's page, directions in the user's own maps app, "Share this place", a shortlist, and a suggest-a-change link.
- **Phone-first:** bottom-sheet popup, **Near me** (the location stays in the browser), dark mode, sport glyph pins at high zoom, and add to home screen (web manifest, no service worker). An automated accessibility check (axe-core) passes in light and dark; a layout, contrast and colour-blind check is in [`docs/sessions/`](docs/sessions).
- **Market insights (inferred):** which racket sports are missing near a city, how many rival venues sit within 5 and 15 miles, and which other sports are nearby. A club sees its local competition and open niches, a player sees where to try something new, and `make market-snapshot` keeps a history to spot openings and closures. Known venues only, no population yet; ask in plain English with a free local model via `ingestion/ask.py` (it picks vetted queries, never writes SQL): [`docs/market_insights.md`](docs/market_insights.md).
- **Quality checks:** dbt tests, a coverage report and a `make quality` scorecard with freshness service levels catch bad data and stale entries ([`docs/data_quality.md`](docs/data_quality.md)).

Mission ([ADR 0015](docs/decisions/0015-mission-and-social-phase.md)): one map for every racket sport in California and Nevada: find a court, watch a match, try a new racket sport, and find people to play with.

## What the data showed
Numbers are dated and come from the notes linked in each row.

| Finding | What it means |
|---|---|
| **No single source is enough.** 27,493 OSM court and facility records plus Overture places became 10,268 venues; 4,526 had a name ([snapshot, 10-22](docs/coverage_snapshot.md)). | OSM knows where courts are, business listings know names. Joining them is the product. |
| **The map is mostly tennis.** Of the 81 sports on the master sheet, 35 are covered and 39 have nothing found ([snapshot](docs/coverage_snapshot.md)). | Gaps are the story for lesser-known sports, so the app shows them instead of hiding them. |
| **Duplicates were inflating the count.** Merging courts inside one park or school, and places at one street address, cut venues from 10,542 to 10,235 (-3%). A guard test now fails if two venues share a name within 150 m. | Fix the cause, then add a test so it cannot return. |
| **About 90% of venues had no street address** ([ML plan](docs/ml_plan.md)). | Most are park and school courts. Now 4,291 of 10,277 venues show one (OSM tags, nearest Overture address or Nominatim, the last two labelled "inferred"), and every pin has a city; homes show the city only, by design. Filling the rest needs a different source, not a better lookup. |
| **Pickleball hides on tennis courts.** Painted lines are rarely tagged, so a re-extract cannot find them; city park pages and owner reports did ([ML plan](docs/ml_plan.md)). | Refreshing data does not fix a data gap; a different source does. |
| **Gyms and public facilities hold niche sports.** Chain and city pages added racquetball (105 venues: CA 90, NV 15) plus YMCA pickleball ([gym scan](docs/gym_chain_scan.md)). | Chain-by-chain scans beat generic search for sports like racquetball. |
| **Websites go bad.** One club domain was hijacked and another belonged to a club in a different state. | Links are checked and flagged (`make check-websites`), not trusted. |

## ML strategy: small models suggest, people decide
Rule: **a model may rank or suggest; it never writes to the map.** Anything inferred is labelled as such. Full plan: [`docs/ml_plan.md`](docs/ml_plan.md).

| Phase | What | Result so far |
|---|---|---|
| 1. Review-queue ranker (built) | Logistic regression on 90 human confirm/reject labels orders about 200 uncertain sport matches, so review time goes to the clearest cases first. | Leave-one-out accuracy 86%, AUC 0.93. |
| 2. LLM reads public pages (built, not run at scale) | Extracts sport, court count and access from a venue's own page; every field needs an exact quote that code checks is on the page ([ADR 0017](docs/decisions/0017-llm-page-reader.md)). | Free rules engine measured; the Claude run waits on an API key, a spend cap and a precision bar. |
| 3. Courts in aerial photos (pilot) | Object detector on free NAIP imagery, trained on OSM court shapes. | Hawthorne: found 8 of 9 mapped tennis courts and 2 new sites; sport and access cannot be seen. |

Lessons worth keeping:
- **Label skew bites.** Every early Tennis label was a reject, so the ranker learned "Tennis means reject". Confirming real tennis clubs fixed it (Tennis likely-rejects 25 to 4). Check what a model learned, not just its score.
- **No leaks.** The confidence score is not a feature, because human overrides already feed it.
- **Honest limits.** The aerial pilot finds single digits of new sites per city, not hundreds, so it is a lead generator for OSM, not a data source.

## How it fits together
![Architecture: sources, Python ingestion, a dbt project on DuckDB, and the static map app](docs/architecture.svg)

```
OSM, Overture, Census, Google Sheet, hand-edited seeds (each with evidence)
  -> Python ingestion -> raw CSV -> DuckDB -> dbt (staging, intermediate, core, marts)
  -> export -> venues.json -> static MapLibre page on GitHub Pages
```

| Stage | Where | Gate |
|---|---|---|
| Ingest | [`ingestion/`](ingestion) | `load_raw.py` refuses to shrink a table by more than 10% |
| Transform | [`transform/`](transform) | dbt tests, hand-labelled gold set for the place-to-court match |
| Ship | [`app/`](app), [`.github/workflows/`](.github/workflows) | CI on a small fixture dataset, export freshness, scorecard no-regression |

There is no server or API: the map reads one exported file, `app/data/venues.json`. Phone numbers are never exported. Layout and layer table: [`docs/architecture.md`](docs/architecture.md); all tools and strategies: [`docs/tools_and_strategies.md`](docs/tools_and_strategies.md). The problem, choices and trade-offs in longer form: [`docs/case_study.md`](docs/case_study.md).

## Workflow and automation
- **Twice-monthly refresh:** sync sports, extract, load, fill addresses, build, export, quality scorecard, PR, CI, deploy ([runbook](docs/monthly_refresh.md)).
- **Suggest a change:** a form or issue, a reviewer adds the `approved` label, a GitHub Action opens a PR that edits one seed row, CI gates it, then merge ([ADR 0008](docs/decisions/0008-contributors-and-confirmation-workflow.md)).
- **Community reports:** a Google Form (no sign-in) or a GitHub issue; the owner approves, then `make sync-reports` imports it as a seed edit ([plan](docs/community_reports_plan.md), [`CONTRIBUTING.md`](CONTRIBUTING.md)).
- **Scheduled refresh, five chained agent runs:** on the 1st and 15th at 09:00 a Claude Code scheduled task starts Part 1, and each part ends by starting the next, so the five run in order and never overlap. Each part is its own session (no subagents) with one job: (1) tennis, pickleball, ITF events, (2) badminton, racquetball, table tennis, squash, (3) padel calendar, beach tennis, padel lead rechecks, (4) Instagram sweep and player-group links, (5) the data refresh runbook with its quality gates. Parts 1-4 add to one tournament PR per cycle; Part 5 opens its own PR stacked on it. They read public pages only and record what they could not read. A merge gate (a script, not a model) merges the refresh PR by itself when it stays inside the R0 limits; tournament PRs are merged by a person, and re-date every event they re-confirm so the freshness SLA stays honest ([steps](docs/tournament_run_parts.md), [source runbook](docs/tournament_refresh.md), [refresh agent](docs/refresh_agent.md)).
- **Agent-assisted, gate-checked:** agents propose changes with evidence, automated gates verify them (dbt tests, CI, freshness, scorecard no-regression, diff cap, evidence required), and people still merge. The draft-mode refresh agent is the last link of the scheduled chain; a kind of change may auto-merge only after it has earned that and the owner switches it on ([ADR 0019](docs/decisions/0019-unattended-agent-merges.md), [plan](docs/self_service_plan.md), [`docs/refresh_agent.md`](docs/refresh_agent.md)).

**Skills shown:** SQL and dbt modelling with tests, entity resolution across messy sources, data-quality scorecards and freshness SLAs, CI/CD gates and GitHub Actions automation, small ML with leave-one-out validation, guard-railed LLM and agent workflows, written decision records ([ADRs](docs/decisions)), and scoping work by cost and risk (privacy, terms of use, honesty).

## For builders and AI tools
The map reads one public file, `app/data/venues.json` (about 2.4 MB, rebuilt about twice a month). Keys are single letters, so read the [data dictionary](app/data-dictionary.md) first; [`app/llms.txt`](app/llms.txt) is the short guide for AI tools. Both are published next to the map. A read-only MCP server over the file is proposed, not built ([ADR 0023](docs/decisions/0023-read-only-mcp-server.md)).

## Privacy and trust
- **No accounts, no cookies, no personal data.** Anonymous visit counts use GoatCounter (cookie-free, honours Do Not Track, counts only named events, never what a visitor typed; [ADR 0013](docs/decisions/0013-usage-analytics.md)).
- **Location stays in your browser** ("Near me" is never sent anywhere). Phone numbers are never exported; homes show the city only.
- **Nothing is invented:** inferred names, sports and addresses are labelled as inferred ([ADR 0007](docs/decisions/0007-confirmation-levels-and-leads.md)).
- **Open data only:** Overture and OSM, with attribution in the app ([`NOTICE.md`](NOTICE.md)).

## Quick start
```bash
pip install -r requirements.txt
make demo       # extract -> load -> build -> test (extract takes ~15 min)
make app-data   # export the map data
make app        # open http://localhost:8765
```
`make build` runs the dbt seeds, models and tests; it is the main check after any change to `transform/`. A new checkout without a database: `make fresh-db` (about a minute; loads the shared raw CSVs and runs the full build). On Windows, `view_db.bat` opens `courtconnect.duckdb` read-only in the DuckDB UI (close it before running dbt).

## Editing the data
Data lives in seeds under `transform/seeds/`; edit them, then `make build` and `make app-data`.

| To change | Edit |
|---|---|
| The list of sports | The Google Sheet, then `make sync-sports` (never hand-edit `all_racquet.csv`) |
| Add a venue no dataset knows | `manual_venues.csv` |
| Add a link-out (open play, lessons, ...) | `venue_actions.csv` |
| Add an event to watch | `watch_events.csv` |
| Confirm or reject an uncertain match | `place_sport_overrides.csv` |
| Mark an Overture place as closed | `closed_places.csv` (with evidence) |
| Correct a court count for one sport at a venue | `venue_court_counts.csv` (with evidence; add the missing sport via `manual_venues.csv`) |

Details: [`docs/data_guide.md`](docs/data_guide.md). Twice-monthly refresh routine: [`docs/monthly_refresh.md`](docs/monthly_refresh.md). Decisions: short records in [`docs/decisions/`](docs/decisions) (ADRs 0001 to 0024; 0001 is superseded by 0018; 0023 and 0024 are proposed).

## Principles
- **Honesty over polish:** inferred data is labelled as inferred.
- **Link out, never transact.**
- **Open data only:** Overture + OSM; Google Places is not used because its terms forbid storing it ([ADR 0005](docs/decisions/0005-overture-places-and-google-terms.md)).
- **Public pages only:** no use of anyone's logged-in accounts ([ADR 0007](docs/decisions/0007-confirmation-levels-and-leads.md)).
- Models run on **DuckDB** (Snowflake support retired 2026-10-14). Data licenses: [`NOTICE.md`](NOTICE.md).

## Roadmap
Done:
- [x] Venue clustering, statewide extract, Overture second source, watch events, link-outs, suggest-a-change flow, duplicate guard
- [x] California + Nevada ([ADR 0014](docs/decisions/0014-calneva-scope.md)): 545 Nevada venues live; resort and casino courts closed by the owner (2026-10-17)
- [x] Street addresses and a city on every pin (OSM tags, nearest Overture address, Nominatim, Census boundaries; inferred ones labelled; homes show city only)
- [x] Every sheet sport in the dropdown (81), with About cards and blurbs; sports with no place yet are greyed "(none yet)" with a report-a-venue link, never fake pins ([`docs/sport_discovery_plan.md`](docs/sport_discovery_plan.md))
- [x] Padel kept apart from pop tennis, every Padel pin audited, directories swept, "Opening soon" pins ([`docs/padel_scan.md`](docs/padel_scan.md))
- [x] Social phase A: find people to play with (player-matching app links, Watch & Social view with recurring open-play series); anything further, such as own accounts, only after a separate decision ([ADR 0024](docs/decisions/0024-social-phase-b.md))
- [x] Visual polish PRs 1-6 (brand tokens, shape and motion, sport icons, friendlier states, popup grouping and status band, glyph pins), front-door promise lines and About dialog, Near me, add to home screen, axe accessibility pass
- [x] Market insights v1, `llms.txt` and a data dictionary, extra analytics events, a draft-mode refresh agent
- [x] Phone and accessibility follow-ups: 44 px touch targets, a tick / "?" badge on zoomed pins so status does not rely on colour, Near me distances (nearest-first lists), better glyph and chip contrast, and a computed "(north courts, 6 courts)" suffix that tells apart venues sharing an inferred name
- [x] Load time measured on throttled Slow 4G / Fast 3G: fine for the beta ([`docs/sessions/2026-10-23-load-time.md`](docs/sessions/2026-10-23-load-time.md))

Next, in order (details in [`CLAUDE.md`](CLAUDE.md) "Open, in order"):
- [ ] Beta prep (owner): exclude your own visits in GoatCounter on each device, then send the invites
- [ ] Beta feedback round with friends (December; [`docs/feedback_round.md`](docs/feedback_round.md)), then rank what to build with the findings
- [ ] Facility scans (UC and CSU campuses, military MWR) and club-named venues, one family at a time
- [ ] Prove the scheduled chain end to end on a real 1st/15th run (each part starting the next unattended), then watch spend against the $20/month ceiling
- [ ] Review queue (116 rows, parked: needs the page reader or community reports) and ML phase 2-3 (Claude page-reader run waits on an API key, a spend cap and a precision bar; the aerial pilot is not worth scaling, [`docs/ml_plan.md`](docs/ml_plan.md))
- [ ] After the beta: cost tier, Watch events split on-site vs screening ([ADR 0022](docs/decisions/0022-watch-event-format-split.md)), optional read-only MCP server ([ADR 0023](docs/decisions/0023-read-only-mcp-server.md))
