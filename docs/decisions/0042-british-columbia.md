# 0042. British Columbia (Canada's first province)

Date: 2026-11-26. Status: proposed; groundwork only. The owner asked for British Columbia "with everything the other regions got". This lifts, for BC only, the 2026-11-13 pause on new-state sessions. Nothing is extracted yet.

## Context
BC is the first Canadian region and the second country after Mexico (ADR 0034). It borders WA and ID and shares the Salish Sea with Washington, so Vancouver and Victoria are close to the existing home view. About 5.6 million people; the metros are Metro Vancouver, Greater Victoria, the Okanagan (Kelowna), Kamloops, Nanaimo and the Fraser Valley. Pickleball, tennis, badminton, table tennis, squash and padel are all strong there.

## Decision
- One region `BC` (OSM relation 390867, name `british_columbia`, country `CA`, blank `fips`), as Mexico is one region. The code `BC` never clashes with California's `CA`, but `country: "CA"` is Canada: keep the two apart in scripts.
- `"defer": true` until the owner approves the extract, so `make extract` and the default Overture read skip it. `--area british_columbia` and `--region BC` still work.
- Groundwork built 2026-11-26: the `regions.json` entry, the dbt `regions` var, the BC line in `state_outline.json` (from Nominatim's relation polygon, simplified), and 10 border test points in `ci/check_regions.py` (Vancouver, Kelowna and others as BC; Blaine and Bellingham as WA; Banff, Calgary and Whitehorse as `None`). Victoria moved from `None` to `BC`.
- Verified 2026-11-26 on Overpass (openstreetmap.fr mirror): relation 390867 is `CA-BC`, admin level 4, bounds 48.2246 / -139.0613 / 60.0021 / -114.0541, inside the `regions.json` box. No change needed.
- Country plumbing built 2026-11-26 (no data yet): Canada option in the app Country dropdown (shown once BC pins exist; `home_shortcut: "country"`), `BC` in the region sentence everywhere, a Canada paragraph in About, `zipNote()` (postal-code search is out of scope; the app says to search the city), `extract_overture_boundaries.py --country CA` (`make extract-boundaries-ca`, regional districts + municipalities, state_fips `CA-BC`), `build_places_lookup.py --ca` (BC city search from those localities), `place_from_boundaries.py` labels BC regional districts without " County", a BC row in `ci/fixtures/osm_courts_bc.csv`, and a logged-empty `zip codes` row. Already generic, so unchanged: the address extractor (`--region BC` reads country `CA`; Canadian address order is number then street, as in the US), `reverse_geocode_blanks.py`, `int_venue_address.sql` (addresses are only kept within ~440 m of a pin, so none cross the border).
- A default (no `--region`) address rewrite skips deferred regions: re-run `extract_overture_addresses.py --region BC` after it.

## Open work, in order (country list from `docs/new_region_checklist.md`, "Countries")
1. Country plumbing (done except Statistics Canada boundaries, not needed; see above): Overture address filter `country = 'CA'` (`extract_overture_addresses.py`), Overture divisions for places and boundaries (Canada has no Census; Statistics Canada boundaries are a fallback), a Canada entry in the Country dropdown, `country` on the region sentence, a home-view shortcut (BC runs to 60 N, past the home view), postal-code search (Canadian codes like V6B 1A1 do not collide with ZIPs, so a later FSA lookup is possible), `reverse_geocode_blanks.py` address order, `region_parity.py` and the CI fixtures.
2. Extract and load: OSM courts, parents and walls (`--area british_columbia`), Overture places and addresses, build, `make app-data`.
3. Research passes per metro: Vancouver first, then Victoria, Okanagan, Kamloops, Nanaimo. Public parks and rec (City of Vancouver, Burnaby, Richmond, Surrey), Pickleball Canada, Tennis BC, Badminton BC, Squash BC, Table Tennis BC, padel clubs, walls, courts coming soon, events, groups, link-outs.
4. Routines, `docs/status.md` and `docs/monthly_refresh.md` rows.

## Owner questions
- French is not needed for BC. Keep the English UI?
- Metric units and CAD in `rules` text: keep local units as written on the venue page?
- Run all of BC at once, or the Vancouver / Victoria metros first, as Mexico did?

## Rules that carry over
Public pages only, no Google Places, no operator logins, no partnership emails, honest inferred labels, one rule for every region (ADR 0034).
