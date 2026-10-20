# 0020. Sand volleyball courts as "could host" candidates (Pro Sunball)

Date: 2026-10-19. Status: accepted (2026-10-19). Related: ADR 0002 (OSM first), 0004 (extract and naming), 0007
(confirmation levels), 0015 (mission: discover sports beyond pickleball).

## Context
Pro Sunball is on the master sheet (2-4 players, felt rubber ball) but has no venues: no OSM tag exists, no club directory
was found (`docs/sport_directories.md`), and the sheet row has no court size, net height or rules link. Its surface is
"Various". Beach and sand volleyball courts are plentiful and well mapped, so they are the obvious places to try it.

A scan on 2026-10-19 (`ingestion/extract_osm_beach_volleyball.py`) found 1,527 court elements in CA + NV, about 841 sites
within 150 m of each other (787 CA, 54 NV). 669 sites are a single court, 42 have a name, 46 elements are `access=private`.

## Decision
1. **A separate candidate layer, not venues.** Sand courts are NOT added to `osm_sport_map.csv` or the venue pipeline.
   Doing so would put ~800 pins under a sport with no confirmed play and would overclaim. The layer is a list of places that
   could host Pro Sunball, shown only when Pro Sunball is the selected sport (the pattern of hitting walls, `mart_wall_pins`).
2. **Always `confirmation = inferred`.** The popup says the court is a sand volleyball court per OpenStreetMap, that nobody
   has reported Pro Sunball there, and that suitability is not confirmed. No "fits" claim until a public source gives the
   Pro Sunball court size and rules; then `ref_sport_fit` may add an *inferred fit*, still never "confirmed".
3. **Access filter.** Keep `access` = yes / permissive / permit (shown as OSM states it). Untagged access stays as "Access
   not stated" (never "public"). `customers` shows as guests or members. `private` and indoor courts are dropped.
4. **Privacy.** Same rule as other pins: home-like locations get a city, never an inferred street. OSM-tagged streets are
   kept. Cities come from `place_from_boundaries.py`.
5. **Promotion path.** A place becomes a real venue only when the owner or a public page reports Pro Sunball play: add it to
   `manual_venues.csv` with `evidence`. Candidates never auto-promote.
6. **Source and terms.** OpenStreetMap only (ODbL, attribution already shown). Requests use the project User-Agent; no
   personal contact in queries.

## Build (scoped)
- PR 1 (no app change): scan folded into `make extract` and `load_raw.py` (`raw.osm_beach_volleyball`),
  `stg_osm_sand_courts`, `mart_sand_court_pins` (150 m clusters via the `int_wall_clusters` logic, park/club name from
  `int_court_parent`, court count), `sand` array in the export, dbt tests (region is CA/NV, confirmation not null).
- PR 2: app layer and a Pro Sunball dropdown entry, then `make app-data` and a `pages.yml` run.
- Later: a public Pro Sunball court-size source for the inferred fit.

## Consequences
Gives Pro Sunball a starting map at low cost and keeps the "discover new sports" goal honest. Risks: OSM sand/volleyball
tags sometimes sit on resort or residential courts, so the access label matters; most sites are one court and unnamed, so
pins will often read "Sand volleyball court near <park or city>". Refresh with each OSM extract.
