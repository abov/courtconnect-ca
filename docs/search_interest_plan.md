# Search interest (Google Trends)

Status: BUILT 2026-10-25 (first export 2026-10-25). Refresh runs from the cloud routine "RacketConnect search interest refresh (quarterly)" (`docs/cloud_routines.md`; quarterly, opens a PR; a person merges). The cloud run has no browser pane: it tries WebFetch once and stops if no real `comparedgeo` values load (never estimates); a full read needs a local run in the browser pane.

**Goal:** an internal planning signal: where do people search for a sport but we have few pins? It picks the next facility scan or lead pass. It is NOT shown on the map and is not a ranking of venues. `make interest` prints it.

## What is in the repo
- `transform/seeds/search_interest.csv`: one row per query geo (`US-CA` / `US-NV`), metro, sport. `index_value` is Trends' relative interest (100 = the top metro of that query), blank = Trends had no data (never 0). `query_set` A = the five busiest sports (tennis, pickleball, padel, badminton, table tennis), B = low-volume terms (racquetball, squash court, beach tennis, pop tennis, platform tennis), which Trends samples, so they are labelled `thin` and never flagged.
- `transform/seeds/search_metros.csv`: the Google metro codes for the covered states (CA, NV, AZ, NM and, since 2026-11-12, six Texas metros; Trends data exists only for CA + NV so far), each with one anchor city.
- `int_search_interest`: puts the CA and NV queries on one scale (Reno is in both, so Las Vegas is rescaled by Reno's ratio; no Reno data = no Las Vegas index).
- `mart_search_vs_coverage`: per (metro, sport) interest next to the venues nearest that metro's anchor. Raw counts favour big metros (and wide 120-mile catchments), so since 2026-11-17 both sides are put on "100 = the average metro" scales: `interest_vs_avg` (the index against the sport's mean) and `supply_index` (the sport's share of the metro's pins against its share across metros with data; all of a metro's pins stand in for its size, so no population seed and the same catchment on both sides). Since the same day the sport's pins are weighted by completeness (`usable_venues`: each pin 0.5 + 0.5 * its share of real name, address and usable website; home-like pins 0.5, as they never get a street or website), so a metro full of bare pins shows less supply; the metro-size count stays raw. `gap_score` = interest_vs_avg / supply_index. `gap_candidate` = confidence ok, interest_vs_avg >= 100, supply_index < 90 and gap_score >= 1.5 (replaced "index >= 50 and 3 or fewer venues", which only caught tiny metros). A place to look for missing venues first, not proof of a gap. Thin sports get a score and their own "weak hints" list in the report, never a flag.
- `ingestion/search_interest_report.py` (`make interest`): prints the report and writes `docs/search_interest_vs_coverage.csv` (metro, sport, index, venues, completeness share; no venue rows). Commit it after a refresh: the Evidence dashboard reads it ("Search interest against coverage", `dashboard/README.md`), and `pages.yml` rebuilds when it changes. Test `assert_search_interest_valid`.

## Limits (say them whenever the numbers are quoted)
- Relative and sampled: an index is the share of a metro's searches, not a count of people. 100 is only the top metro of that sport and query, so compare metros within a sport, not sports with each other.
- Venues are assigned to the NEAREST anchor city within 120 miles: our own approximation. Nielsen owns the DMA county boundaries and forbids redistributing them, so we do not store a county-to-DMA list. Border and rural pins can land in the wrong metro.
- "Yuma AZ-El Centro" includes Yuma searches (Arizona), so a gap there is weak. Out-of-region metros Trends returns (Medford OR, Salt Lake City UT) are dropped from the seed.
- Padel in Las Vegas: NV resort/casino courts follow the all-states resort rule (ADR 0028, reopened 2026-11-02); the 2026-10-17 passes stand, so a Las Vegas gap is not a reason to redo them.

## Refresh procedure (about quarterly; the routine follows this)
Read-only use of the public Trends pages in the built-in browser pane: no sign-in, no download, no `pytrends`, no API. Take no screenshots.
1. For each of the 4 URLs in `source_url` (geo `US-CA`/`US-NV` x query set A/B; only change the sport list if the sheet's sports change): open the URL in the browser pane, wait 5 s, scroll down once so every widget loads.
2. `read_network_requests` with `urlPattern=comparedgeo`: the last 5 requests are the five terms in the order of the `q=` list. Read each one by `requestId`; each body is `{"default":{"geoMapData":[{"geoCode","geoName","value":[n],"hasData":[bool]}]}}`.
3. Check the order once: the third response of set A must equal a padel-only query (`q=padel`).
4. Rewrite `search_interest.csv` (same columns; `hasData` false = blank `index_value`; keep only metros in `search_metros.csv`; new `period` and `exported_on`). Keep CRLF.
5. `dbt build --select search_metros search_interest int_search_interest mart_search_vs_coverage assert_search_interest_valid`, then `python ingestion/search_interest_report.py` (also rewrites `docs/search_interest_vs_coverage.csv`; commit it).
6. Open a PR with the report's gap list in the description (2-4 bullets) and a new `docs/sessions/` note. If Trends returns 429 or empty widgets, stop, write the note and do not retry in a loop.
7. Act on the top 2-3 gaps only if the owner asks; otherwise they feed the next facility scan or padel lead pass choice.

## Related queries as leads (pilot 2026-11-17, padel + pickleball, CA + NV)
Method: open the explore page for one term and state (`https://trends.google.com/trends/explore?date=today%2012-m&geo=US-CA&q=padel&hl=en`), scroll down until the widgets load, then `read_network_requests` with `urlPattern=relatedsearches`; the second of each pair is "related queries" (top 25 + rising), the first is related topics (no place names). Keep only queries naming a place or club; drop gear brands, pro tours, generic terms and other states. Check each name against `mart_venue_finder`, `manual_venues.csv` and `venue_leads.csv`; new ones go into `venue_leads.csv` (`source_type=other`, "Google Trends related query" + date in `claim`). Never source a lead's details from Pickleheads or other off-limits directories; confirm from the club's own page before pinning.

Pilot result: 4 pages, about 180 queries, 10 name a place or club. Already on the map: Bay Padel, Padel Up, Park Padel, P1 Padel, Sunset Park (Las Vegas), Vegas Indoor Pickleball, Pickleball City (Fremont). New lead: West Coast Pickleball Pomona (rising +1,700%; the club's page says opening 2026, no address yet; lead `wcpb-pomona-pickleball`). No venue found: GamePoint Pickleball, RPM Pickleball (RPM looks like a paddle brand). Hit rate: 1 new lead from ~180 queries (1 of 10 place names). The lists are mostly gear, and the clubs people search for are the big ones we already have; the rising list is where the one new club showed up.

Verdict: cheap (about 10 minutes for 4 pages) but low yield. Not worth its own routine; add it to the quarterly refresh only as an optional step for the two or three gap sports (`gap_candidate`), reading the rising list, where a newly opened club shows up first.

## Not now (kept here so it is not lost; revisit after the beta, ADR 0015)
- Showing trends in the app (a "trending sport" badge, per-venue demand): guesses presented as fact, so no.
- Metro-level per-capita comparison: needs metro population (a second seed); the pin-mix `supply_index` stands in for it. Region level is done (below). Revisit if a metro dominated by one sport (Palm Springs: 93% tennis pins) misleads.
- Cross-sport comparison on one scale: needs the interest-over-time averages per state.
- Auto-fetching Trends or an official API: revisit if a stable one appears.
- Cities below metro level: Trends has no stable city-level pages for these terms.

## Pins per million people (2026-11-24)
- `mart_pins_per_million` (seed `region_population`: 2020 census / INEGI Censo 2020, state or country level) gives pins per million people for every region, in total and per sport. `make interest` prints it.
- It stands in for search interest where Trends has no data (Trends: CA + NV only; Mexico none). 2026-11-24: HI 311, AZ 308, OR 283, WA 271, CA 255, NM 253, TX 190, NV 176, MX 15 (ADR 0034 expected 15-40).
- Limits: it measures supply, not interest or demand; a low number can mean few courts or few we found. Region-wide counts hide metro differences (Mexico's pins sit in a few metros), and a state's tourists and snowbirds are not in its census population. No metro-level populations yet.
