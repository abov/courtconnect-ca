# New state / country checklist

Owner 2026-11-03: every new state (and country, ADR 0034) gets the same work the others got, with nothing left silent. This is the one list; ADR 0028 ("Per-state step") is the reasoning behind it. Arizona's first PR (#525) shipped the data layer only, and the home view hid its southern border: this list and `ci/region_parity.py` exist so that does not repeat.

**Rule:** a region is not "done" until `python ci/region_parity.py --region XX --strict` exits 0 and every other zero in its column is either filled or logged below its section in `docs/event_group_search.md` / `docs/public_facility_scan.md` as "searched, empty". Put the printed column in the PR description.

## 1. Data layer (one PR, mostly configuration)
- [ ] `ingestion/regions.json` entry (bbox, OSM relation checked against Overpass, `fips`, cache file) and the `regions` var in `transform/dbt_project.yml`; test points in `ci/check_regions.py` (cities inside, neighbours across each border, and a nearby foreign city as `None`).
- [ ] Extract: OSM courts + parents (`--area <name>`), Overture places + addresses, `load`, `build`, `reverse_geocode_blanks.py`, `make city-boundaries`, `make extract-boundaries` (Census places), `make app-data`.
- [ ] `app/data/state_outline.json` via `python ingestion/add_state_outline.py`, ZIPs (`zips.json`) and places (`places.json`): in the app and drawn.
- [ ] **Home view**: `HOME_BOUNDS` in `app/index.html` contains the region with at least 0.25 degrees to spare on every side (the parity script checks it); far-away regions (Hawaii, Mexico) get a shortcut instead.
- [ ] **Region sentence** everywhere: `REGION` and the static repeats in `app/index.html` (title, meta, About, loading text), `app/llms.txt`, `manifest.webmanifest`, `app/data-dictionary.md`, README line 3, the issue form, dbt exposure and overview, `ingestion/ask.py`. `grep -rn "Oregon, Washington"` finds them.
- [ ] CI fixtures: one row for the region in `ci/fixtures`.

## 2. Research passes (the large cost; same PR or a named follow-up)
- [ ] **Hand-added venues** `manual_venues.csv` (with `region`): city parks and rec, YMCA, Life Time / 24 Hour / LA Fitness (`docs/gym_chain_scan.md`), campuses, military (rule in ADR 0014), private clubs, resorts case by case (ADR 0028). Scan notes in `docs/public_facility_scan.md`.
- [ ] **Walls**: `extract_osm_walls.py --area <name>` (not part of `make extract`), plus `manual_walls.csv` from official rec pages; handball, wallball, backboards. Hawaii and Washington are still at zero hand-added.
- [ ] **Link-outs** `venue_actions.csv` for hand-added venues (booking, drop-in, league), with `verified_on` + `evidence`.
- [ ] **Events and groups** ("find your people", `docs/event_group_search.md`): `watch_events.csv`, `social_events.csv`, `player_groups.csv`, leagues; every sport the region has venues for, and the national-body section pages. Log searched/empty/recheck in the region's section.
- [ ] **Padel, pop tennis, beach tennis, squash, table tennis, badminton, racquetball** passes (`docs/padel_scan.md`, `beach_tennis_watch.md`); a zero is fine only if logged as searched.
- [ ] Leads you could not settle go to `venue_leads.csv`.
- [ ] Street addresses: `reverse_geocode_blanks.py`, `extract_osm_parents.py` after each OSM refresh; never infer a street for home-like pins.

## 3. Routines and docs
- [ ] Routine source lists (`docs/cloud_routines.md`, `docs/tournament_run_parts.md`, refresh agent, search-interest metros in `search_metros.csv`) extended for the region once its research exists.
- [ ] `docs/monthly_refresh.md` rows, `docs/status.md` priority line, ADR status line (what is built, what is open).
- [ ] After the extract, refresh the private raw-data repo.

## 4. Before saying "done"
1. `python ci/region_parity.py --region XX --strict`
2. Full `dbt build`, `make app-data` committed, `python ci/check_regions.py --config-only`.
3. Open the map: home view shows the whole outline with room around it; search a city and a ZIP in the region; a pin popup, a wall, an event.
4. Say in the PR what is still empty and why. Never call a state done with an unlisted zero.

## Countries (ADR 0034)
Same list, plus: a country outline in `state_outline.json`, a home-view shortcut like Hawaii's, ZIP/postcode copy, language of `rules` text, and a "no Google/operator data" check for each local source. Write the country's own section in this file when the first one starts.
