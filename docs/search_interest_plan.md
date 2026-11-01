# Search interest (Google Trends)

Status: BUILT 2026-10-25 (first export 2026-10-25). Refresh runs from the scheduled task `courtconnect-search-interest-refresh` (quarterly, opens a PR; a person merges).

**Goal:** an internal planning signal: where do people search for a sport but we have few pins? It picks the next facility scan or lead pass. It is NOT shown on the map and is not a ranking of venues. `make interest` prints it.

## What is in the repo
- `transform/seeds/search_interest.csv`: one row per query geo (`US-CA` / `US-NV`), metro, sport. `index_value` is Trends' relative interest (100 = the top metro of that query), blank = Trends had no data (never 0). `query_set` A = the five busiest sports (tennis, pickleball, padel, badminton, table tennis), B = low-volume terms (racquetball, squash court, beach tennis, pop tennis, platform tennis), which Trends samples, so they are labelled `thin` and never flagged.
- `transform/seeds/search_metros.csv`: the 14 Google metro codes covering CA + NV, each with one anchor city.
- `int_search_interest`: puts the CA and NV queries on one scale (Reno is in both, so Las Vegas is rescaled by Reno's ratio; no Reno data = no Las Vegas index).
- `mart_search_vs_coverage`: per (metro, sport) interest next to the venues nearest that metro's anchor. `gap_candidate` = confidence ok, index >= 50 and 3 or fewer venues. A place to look for missing venues first, not proof of a gap.
- `ingestion/search_interest_report.py` (`make interest`), test `assert_search_interest_valid`.

## Limits (say them whenever the numbers are quoted)
- Relative and sampled: an index is the share of a metro's searches, not a count of people. 100 is only the top metro of that sport and query, so compare metros within a sport, not sports with each other.
- Venues are assigned to the NEAREST anchor city within 120 miles: our own approximation. Nielsen owns the DMA county boundaries and forbids redistributing them, so we do not store a county-to-DMA list. Border and rural pins can land in the wrong metro.
- "Yuma AZ-El Centro" includes Yuma searches (Arizona), so a gap there is weak. Out-of-region metros Trends returns (Medford OR, Salt Lake City UT) are dropped from the seed.
- Padel in Las Vegas: NV resort/casino courts are closed (owner 2026-10-17); a Las Vegas gap means look at non-resort sources only.

## Refresh procedure (about quarterly; the scheduled task follows this)
Read-only use of the public Trends pages in the built-in browser pane: no sign-in, no download, no `pytrends`, no API. Take no screenshots.
1. For each of the 4 URLs in `source_url` (geo `US-CA`/`US-NV` x query set A/B; only change the sport list if the sheet's sports change): open the URL in the browser pane, wait 5 s, scroll down once so every widget loads.
2. `read_network_requests` with `urlPattern=comparedgeo`: the last 5 requests are the five terms in the order of the `q=` list. Read each one by `requestId`; each body is `{"default":{"geoMapData":[{"geoCode","geoName","value":[n],"hasData":[bool]}]}}`.
3. Check the order once: the third response of set A must equal a padel-only query (`q=padel`).
4. Rewrite `search_interest.csv` (same columns; `hasData` false = blank `index_value`; keep only metros in `search_metros.csv`; new `period` and `exported_on`). Keep CRLF.
5. `dbt build --select search_metros search_interest int_search_interest mart_search_vs_coverage assert_search_interest_valid`, then `python ingestion/search_interest_report.py`.
6. Open a PR with the report's gap list in the description (2-4 bullets) and a new `docs/sessions/` note. If Trends returns 429 or empty widgets, stop, write the note and do not retry in a loop.
7. Act on the top 2-3 gaps only if the owner asks; otherwise they feed the next facility scan or padel lead pass choice.

## Not now (kept here so it is not lost; revisit after the beta, ADR 0015)
- Showing trends in the app (a "trending sport" badge, per-venue demand): guesses presented as fact, so no.
- Per-capita comparison: needs metro population (a second seed); worth it only if the first gap lists mislead.
- Cross-sport comparison on one scale: needs the interest-over-time averages per state.
- Auto-fetching Trends or an official API: revisit if a stable one appears.
- Cities below metro level: Trends has no stable city-level pages for these terms.
