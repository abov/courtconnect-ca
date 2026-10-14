# CalNeva audit: hard-coded California assumptions (2026-10-14)

Read-only grep of code, models, tests, app, CI and docs. Nothing was changed. Generated paths (`transform/target`, `venues.json`, DuckDB file) were skipped. Counts of `California`/`CA` mentions: 126 in code/docs, about 1,400 in CSVs (mostly raw data columns, which are fine).

## A. Logic that must change (blocks Nevada data)

| Where | What is hard-coded | Change |
|---|---|---|
| `ingestion/overpass.py:17-26,91-119` | `BBOXES` are CA metros only; `california_tiles()` uses 32.5/42.1/-124.5/-114.0; `california_border()` builds the CA polygon from OSM relation 165475, cached at `data/raw/ca_border.wkt`; `in_california()` clips every extract | Make a region table (CA, NV) with bbox, OSM relation id and cache file; `tiles(region)`, `in_region(lat, lon, region)`. NV relation id to look up and verify. Add NV metro bboxes (Las Vegas/Henderson, Reno/Sparks, Carson City, Tahoe) |
| `ingestion/extract_osm_courts.py`, `extract_osm_parents.py`, `extract_osm_walls.py` | `--area california`; each calls `in_california`; a comment says "drop Nevada" | Add `--area nevada` / `--region`; add a `region` column to the raw CSVs. Walls `metros` list gets NV metros |
| `ingestion/extract_overture_places.py:72,85` | SQL bbox `-124.5..-114.0 / 32.5..42.1`, then `in_california` clip; message text says California | Run per region (or union bbox then clip to either border); keep Overture's `region` field (`addresses[1].region`) as a cross-check |
| `ingestion/import_paddle_tennis_map.py:56-112` | Geocoder strings append ", California" and parse ", CA" | Only matters if the source has NV rows; take the state from the row |
| `transform/tests/assert_courts_inside_california.sql`, `assert_manual_venues_inside_california.sql` | Fail if outside CA bbox (32.5-42.1, -124.5 to -114.1) | Rename to `..._inside_region`; allow CA bbox or NV bbox (NV spans about 35.0-42.0, -120.0 to -114.0). Bbox overlap near Tahoe means this is a sanity check only; the border clip is the real filter |
| `transform/models/core/dim_sport.sql:21-22` | `likely_in_california` from `loc_lc like '%ca%'` (crude, also matches any "ca" substring) | Rename `likely_in_calneva`, match `%ca%` / `%nv%` / `nevada` properly; check who reads the column |
| `app/index.html:403-410,537` | Initial map bounds and "fit all" use `[[-124.6, 32.4], [-114.0, 42.2]]` | NV extends to about 35.0 N and -114.04 W; CA bbox already covers its east edge, so the box nearly fits. Check Nevada's far north-east (-114.04) and use one shared `REGION_BOUNDS` constant |
| No `state`/`region` column anywhere in models or `venues.json` | Region is implied by the bbox | Add `region` (CA/NV) at the raw layer (set by the extractor that found it, verified by the border polygon), carry it through `dim_venue`, mart and export, so the app can filter and label by state |

## B. Labels to rename (California -> CalNeva)

- App: `<title>`, meta description, `<h1>` (lines 6, 9, 130), map `aria-label` (211); check "statewide" wording and the footer.
- `Makefile` lines 8-13 (help text; target flags change with section A).
- `ingestion/export_coverage_report.py:52` heading "California coverage snapshot"; line 76 "statewide".
- Docs: `README.md` (8), `CLAUDE.md` title and intro, `CONTRIBUTING.md`, `docs/case_study.md`, `docs/roadmap_phase2.md`, `docs/feedback_round.md`, `docs/outreach/bracketsync.md`, `docs/sport_directories.md` (17, mostly search queries, leave as history), `docs/tournament_refresh.md` (10) and `docs/tournament_sources.md` (17) (these are source lists: add NV rows, do not rewrite CA ones), `docs/architecture.svg` (3).
- dbt: `models/exposures.yml` (2), `mart_sport_gaps.sql` (2), `mart_sport_surface_coverage.sql` (1), `assert_watch_events_valid.sql` (1; check what the CA reference does).
- ADRs: leave 0001-0013 as history; ADR 0014 records the scope change.
- CI fixtures (`ci/fixtures/*`) are CA samples; add 1-2 NV rows so CI exercises the region logic.

## C. Leave as is

- Repo, folder and Pages URL names (`courtconnect-ca`) until the owner decides.
- Raw data columns that contain "CA" as an address state (`overture_places.csv`, `osm_parents.csv`).
- Seeds: existing CA rows. New NV rows need the region and the same `evidence`/`verified_on` rules.
- `.github/workflows` and `ci/*.py` have no California references.

## D. Risks and open questions

1. **Tahoe and border towns:** a bbox overlap means a court near Stateline/Lake Tahoe can pass one state's bbox and fail the other's polygon; clip with the polygon, test with known points on both sides.
2. **Region key source:** use the border polygon, not Overture/OSM address text (often missing). One venue gets one region.
3. **Sport sheet:** `all_racquet.csv` (75 sports) has a location column used by `likely_in_california`; Nevada sports (any not in the sheet) go through the Google Sheet, never hand-edited.
4. **Overpass load:** a Nevada statewide extract is large and sparse. Use metro slices first (as for walls), statewide later.
5. **Scorecard targets** (`export_quality_scorecard.py`, e.g. named venues goal 25%) are statewide numbers; decide per region or combined.
6. **Name:** "CalNeva" in the app title only, or also in the domain/repo? (owner)

## Suggested order

1. ADR 0014 (scope, region key, what stays CA-specific).
2. `overpass.py` region table + polygon clip, with a unit check on known CA/NV points.
3. `region` column through raw -> dim -> export; app reads it.
4. Rename the labels in section B in one PR.
5. Nevada metro extracts, then seeds and tournaments per the TODO.
