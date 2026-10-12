# Phase 2 plan: complete California coverage

Draft 2026-10-11. Goal: one map where a player can find every racket-sport court in California (public or private), what it is like (indoor/outdoor, lit, hours), where to hit alone (walls), and what tournaments to watch.

Ground rules (from CLAUDE.md / ADRs): Overture + OSM only (ADR 0005), no owner logins (ADR 0007), link out, never book. Every new field carries a confirmation level: `confirmed` (official page or owner report), `tagged` (OSM tag), `inferred` (our guess, labelled as such), `unknown`.

## What already exists
- `stg_osm_courts.sql` already derives `indoor / covered / outdoor` (`indoor`, `covered`, `building` tags), `is_lit` (`lit=yes`) and `opening_hours` (raw OSM string). These are staged but need checking that they reach `dim_court` -> mart -> `venues.json` -> UI.
- `watch_events.csv` + `stg_watch_events` cover **spectator** events (pro tours).
- Access toggle (public / private-members) is done.

## Workstreams

### 1. Court coverage (public and private)
- Measure first: add "courts per sport" and "named venues per city" to `make report`; compare against known lists (city/county rec directories, USTA/USPA/USAPA/USA Racquetball finders: link-out only where terms bar copying).
- Close gaps: Overture/OSM pass for private clubs, schools, HOA/residential courts (labelled private), hotels/resorts, colleges. Unmapped courts go in `manual_venues.csv` with `verified_on` + `evidence`.
- Coverage-by-county view so we can see which counties are thin (rural counties likely).
- Optional: owner fixes OSM tags directly (improves everyone, no licence issue).

### 2. Indoor / outdoor / covered (rain)
- Surface the existing derived field in the UI as a filter: Outdoor / Covered / Indoor, plus a "rain-proof" shortcut = indoor or covered.
- Venue-level rollup: a venue is "has indoor" if any court is indoor/covered (show counts, e.g. 2 indoor of 8).
- Unknown stays unknown. Do not infer indoor from a building name; only `inferred` where a venue's own website says so (record in `venue_actions` evidence).
- Note: OSM `covered` is sparse, so expect many `unknown`. A cheap way to fill: check satellite via owner reports, not scraping.

### 3. Night play: outdoor courts with lights
- Surface `is_lit` as a "Lit for night play" filter, outdoor/covered courts only.
- Tri-state, not boolean: `lit` yes / no / unknown (today `lit != yes` collapses no and unknown, which is dishonest). Fix in `stg_osm_courts`.
- Add `lighting_note` (e.g. "lights on timer until 10pm", "pay-to-light coin box") from seeds/official pages; many public courts have a coin or button system.
- Gap fill: city parks & rec court pages often list lighting; add as `venue_attributes.csv` seed rows with source + date.

### 4. Hours: is it worth it?
Recommendation: yes, but staged, because hours are the field most likely to be wrong and stale.
1. Parse OSM `opening_hours` (many courts have none). Add a small parser (Python `opening_hours` lib or hand rules) producing `open_now`-style structured data; keep raw string. Label `tagged`.
2. Rule-based public-park default: many city parks are "dawn to dusk" or 6am-10pm. Store as `inferred` with the city rule cited, never as confirmed.
3. Lit courts: lighting cut-off time is the useful night number.
4. Hand-curated hours (seed) only for top venues (clubs, big public complexes); show "last verified" date.
5. Always show "check the venue's site" link. Do not build an "open now" filter until >~50% of venues have non-inferred hours.

### 5. Hitting walls (new feature)
Examples: Venice Beach (next to paddle tennis courts, one-wall and three-wall), El Segundo Recreation Park (one-wall paddle practice).
- Model: new entity `dim_wall` (not a court): `wall_id, name, lat, lon, wall_type (one_wall / three_wall / backboard / handball_wall / other), sports_suited (tennis, paddle tennis, platform tennis, pickleball, racquetball, squash...), surface, is_lit, access, free_to_use, near_venue_id, source, confirmation_level, notes/photo link`.
- Sources, in order of cost:
  1. OSM: tag search for `sport=tennis` + `leisure=pitch` with `tennis=hitting_wall`/`wall=*`, `leisure=practice_wall`/"backboard"; handball (`sport=handball`, one-wall handball courts double as hitting walls); `sport=racquetball`. Measure how many exist before building more.
  2. Owner leads (Venice, El Segundo) go straight into a `manual_walls.csv` seed with evidence + photo. This is the main source; walls are rarely mapped.
  3. City parks & rec facility lists (search "tennis practice wall", "backboard", "handball court" by city) as leads.
  4. Contributor form (ADR 0008 workflow): "Add a wall" with location, type, photo.
- UI: new layer/toggle "Hitting walls" with a distinct icon; filter by one-wall / three-wall; popup says which sports it suits (labelled inferred unless reported).
- Open question: three-wall vs one-wall paddle needs wall height and a flat apron; capture `wall_height_m`, `apron_surface` where known.

### 6. Tournaments: watch only
Scope decision 2026-10-11: no "participate/enter" tournaments. Only events to watch.
- Keep using `watch_events.csv` (pro and major events, `watch_format`, tickets, https links only).
- Widen beyond pro tours where spectating is open: college matches, large amateur championships with free spectators. Flag free vs ticketed; label indoor/outdoor and surface from the venue (rain relevance).
- Refresh: quarterly seed pass; `date_status` (confirmed / tentative); hide past events at export.

### 7. Quality, trust and maintenance
- Add dbt tests: lat/lon inside California; `lit` only on outdoor/covered; walls have a source; events have https links and future-or-recent dates.
- Staleness: every seed row has `verified_on`; report counts older than 12 months.
- Nightly/quarterly refresh job decision (ADR needed): only after owner OK (extract is ~15 min).

## Suggested order
| Step | Work | Size |
|---|---|---|
| A | Verify indoor/outdoor/lit/hours flow to the app; tri-state lit; add three filters | small |
| B | Walls: `manual_walls.csv` + `dim_wall` + map layer; seed Venice and El Segundo | medium |
| C | OSM wall tag measurement; add what it finds | small |
| D | Hours: OSM parse + `inferred` park defaults; display with confidence | medium |
| E | Widen `watch_events.csv` beyond pro tours (college, big amateur events) | small |
| F | Coverage-by-county report; private club and school gap passes | medium, ongoing |
| G | Contributor "add a wall / report lights / report hours" flow | medium |

Each step = one session and one PR (CLAUDE.md "one task per session"). Cheapest first: A, then B.

## Notes slot
Add more notes here as you send them:
-
