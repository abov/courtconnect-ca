# 0042. British Columbia (Canada's first province)

Date: 2026-11-26. Status: accepted, in progress (owner 2026-11-26 asked for British Columbia "with everything the other regions got"; this lifts, for BC only, the 2026-11-13 pause on new-state sessions). Data layer and country plumbing are built and `defer: true` is still set; research passes 1 to 13 have merged (see "Where it stands"). Still open: BC walls, events and social series, the places lookup, doc sections and the owner questions below.

## Context
BC is the first Canadian region and the second country after Mexico (ADR 0034). It borders WA and ID and shares the Salish Sea with Washington, so Vancouver and Victoria are close to the existing home view. About 5.6 million people; the metros are Metro Vancouver, Greater Victoria, the Okanagan (Kelowna), Kamloops, Nanaimo and the Fraser Valley. Pickleball, tennis, badminton, table tennis, squash and padel are all strong there.

## Decision
- One region `BC` (OSM relation 390867, name `british_columbia`, country `CA`, blank `fips`), as Mexico is one region. The code `BC` never clashes with California's `CA`, but `country: "CA"` is Canada: keep the two apart in scripts.
- `"defer": true` until the owner approves the extract, so `make extract` and the default Overture read skip it. `--area british_columbia` and `--region BC` still work.
- Groundwork built 2026-11-26: the `regions.json` entry, the dbt `regions` var, the BC line in `state_outline.json` (from Nominatim's relation polygon, simplified), and 10 border test points in `ci/check_regions.py` (Vancouver, Kelowna and others as BC; Blaine and Bellingham as WA; Banff, Calgary and Whitehorse as `None`). Victoria moved from `None` to `BC`.
- Verified 2026-11-26 on Overpass (openstreetmap.fr mirror): relation 390867 is `CA-BC`, admin level 4, bounds 48.2246 / -139.0613 / 60.0021 / -114.0541, inside the `regions.json` box. No change needed.
- Country plumbing built 2026-11-26 (no data yet): Canada option in the app Country dropdown (shown once BC pins exist; `home_shortcut: "country"`), `BC` in the region sentence everywhere, a Canada paragraph in About, `zipNote()` (postal-code search is out of scope; the app says to search the city), `extract_overture_boundaries.py --country CA` (`make extract-boundaries-ca`, regional districts + municipalities, state_fips `CA-BC`), `build_places_lookup.py --ca` (BC city search from those localities), `place_from_boundaries.py` labels BC regional districts without " County", a BC row in `ci/fixtures/osm_courts_bc.csv`, and a logged-empty `zip codes` row. Already generic, so unchanged: the address extractor (`--region BC` reads country `CA`; Canadian address order is number then street, as in the US), `reverse_geocode_blanks.py`, `int_venue_address.sql` (addresses are only kept within ~440 m of a pin, so none cross the border).
- A default (no `--region`) address rewrite skips deferred regions: re-run `extract_overture_addresses.py --region BC` after it.

## Built so far (2026-11-26, first extract)

- BC OSM courts and parents, Overture places (162 rows) and Overture divisions are loaded; the build is green with 1,272 BC pins (81 confirmed, 3 padel, 234 pickleball). `defer` stays true.
- Overture's Canadian address points are all `LicenseRef-Proprietary`, so the ADR 0034 licence filter keeps none; addresses come from OSM tags and cached reverse geocodes (100 per run, ~446 BC pins still blank).
- Not done: BC (and ID/UT) OSM walls (Overpass too slow in one session), the research passes (Vancouver first), manual venues, watch events, links, ZIP/postal lookups, doc sections.
- `assert_padel_has_supporting_signal` exempts BC like MX until the owner rules (3 name/OSM-tag padel pins, shown labelled inferred).

- 2026-11-26, places and walls: `places.json` has 359 BC rows (`build_places_lookup.py --ca`; Vancouver, Victoria, Kelowna, Kamloops, Nanaimo found). 13 BC `manual_walls` (5 Burnaby added from the City's court table). OSM walls still not extracted: Overpass was unreachable from the cloud session; metros vancouver, victoria, okanagan, kamloops and nanaimo are in `regions.json` for `extract_osm_walls.py --area <metro>`. The raw-data repo has no BC/ID/UT files, so no export was made.

- Research pass 1 (2026-11-26, Vancouver padel): Padel FVR Pitt Meadows confirmed, Padel Model re-pinned in Richmond (Overture's point was in Maple Ridge), Graybar Badminton pinned, 3 leads; log in `docs/public_facility_scan.md`.

## Where it stands (2026-11-26, parity run on main 15d9126c)
`python ci/region_parity.py --region BC` (not strict): 1,272 pins (81 confirmed, 88 with a street address), 139 manual venues, 8 hand-added walls, 21 hand-added link-outs, outline and home view ok. By sport: pickleball 234, table tennis 82, badminton 37, squash 17, racquetball 2, padel 3; pop tennis and beach tennis have none (log as searched or search).
- Required items still at zero: OSM walls and every wall-type pin (one_wall, three_wall, backboard, handball), watch events, social series, places (the BC city search is not in `places.json` yet: run `build_places_lookup.py --ca`), doc sections. ZIP codes are logged empty on purpose (postal-code search is out of scope).
- Research merged on main, passes 1 to 14 (PRs #1019 to #1054): Vancouver padel and badminton, Richmond, Vancouver squash, table tennis and walls, Greater Victoria, Okanagan, Nanaimo and Kamloops, Surrey and Fraser Valley, Parksville and Qualicum, Duncan and Cowichan, Whistler and Sea-to-Sky, Northern BC, Peace River and Kootenays, Cariboo and Thompson-Nicola, Tri-Cities, Maple Ridge and Mission, Vancouver Island north of Nanaimo, Cranbrook, Comox Valley, Gulf Islands and Sunshine Coast, North Shore and Burnaby, plus cross-region leads. Logs are in `docs/public_facility_scan.md`; `git log --grep "British Columbia research pass"` lists them.
- Street addresses: Overture's Canadian points are proprietary-licensed (kept none), so most BC pins rely on OSM tags and capped reverse geocoding (88 of 1,272 have one); rerun `reverse_geocode_blanks.py` until the blanks are filled.
- Padel guard: BC is exempt from `assert_padel_has_supporting_signal` like MX until the owner rules.

## Open work, in order (country list from `docs/new_region_checklist.md`, "Countries")
1. Country plumbing (DONE 2026-11-26; was: done except Statistics Canada boundaries, not needed; see above): Overture address filter `country = 'CA'` (`extract_overture_addresses.py`), Overture divisions for places and boundaries (Canada has no Census; Statistics Canada boundaries are a fallback), a Canada entry in the Country dropdown, `country` on the region sentence, a home-view shortcut (BC runs to 60 N, past the home view), postal-code search (Canadian codes like V6B 1A1 do not collide with ZIPs, so a later FSA lookup is possible), `reverse_geocode_blanks.py` address order, `region_parity.py` and the CI fixtures.
2. Extract and load (DONE for OSM courts, parents, Overture places and divisions; OSM walls and the Overture address rerun with `--region BC` are open): OSM courts, parents and walls (`--area british_columbia`), Overture places and addresses, build, `make app-data`.
3. Research passes per metro (in progress, see "Where it stands"; passes 1 to 14 merged; still to do: events and social series, OSM walls): Vancouver first, then Victoria, Okanagan, Kamloops, Nanaimo. Public parks and rec (City of Vancouver, Burnaby, Richmond, Surrey), Pickleball Canada, Tennis BC, Badminton BC, Squash BC, Table Tennis BC, padel clubs, walls, courts coming soon, events, groups, link-outs.
4. Routines, `docs/status.md` and `docs/monthly_refresh.md` rows.

## Owner questions
- French is not needed for BC. Keep the English UI?
- Metric units and CAD in `rules` text: keep local units as written on the venue page?
- Run all of BC at once, or the Vancouver / Victoria metros first, as Mexico did?

## Rules that carry over
Public pages only, no Google Places, no operator logins, no partnership emails, honest inferred labels, one rule for every region (ADR 0034).
