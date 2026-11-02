# 0032. A hitting wall is a venue

Date: 2026-11-02. Status: proposed (owner asked for it in chat 2026-11-02: "a wall is considered a venue in my eyes").

## Context
Hitting walls (1-wall, backboard, 3-wall) are a separate layer: `dim_wall` -> `int_wall_clusters` -> `mart_wall_pins`, exported as `walls` beside `venues`, drawn as orange pins, filtered by a "hitting alone" bar, and tied to sports through the `WALL_SPORT` table in `app/index.html`. `int_wall_venue_link` only points a wall at a venue; "walls never count as courts". Every feature has to special-case them: "Find by court" ignored 1-wall Paddleball because it has walls and no venues (fixed in #494), counts differ, and the popup, search, share link and changes feed each treat walls on their own. To a person a wall is a place to play, so the data should say so.

## Decision
- **One thing, two kinds.** `dim_venue` gains `venue_kind` (`courts`, `hitting_wall`). A wall pin that links to no listed venue becomes a venue of kind `hitting_wall`, with the same id scheme, address tiers, access and confirmation labels, `verified_on`/`evidence`, and entries in `bridge_venue_sport`.
- **A wall at a listed venue is not a second pin.** Where `int_wall_venue_link` matches (name within the name radius, else nearest within the link radius), the wall becomes a feature of that venue ("Hitting walls on site", as today) and the sports it supports join that venue's sports. No duplicate pin.
- **Sports.** The wall type maps to sports in one place (a seed, replacing `WALL_SPORT`): one_wall/backboard -> 1-wall Paddleball, Outdoor Racquetball, Knuckle Racket (public only); three_wall -> 3-wall Paddleball, Outdoor Racquetball, Knuckle Racket. These rows are labelled inferred from the wall type, never confirmed play.
- **1-wall and 3-wall are one thing to a visitor.** "Hitting alone" is a filter on venues (kind `hitting_wall` or any venue with a wall), not a layer, and it shows every wall type together. The wall type stays as a detail in the popup.
- **Counts.** Hitting-wall venues count as venues and in sport totals; `meta` reports `venues` and `hitting_walls` separately so the headline can say both. Walls stacked side by side keep one pin with `wall_count`.
- **Honesty rules unchanged.** Wall size is the sport's standard, not measured; access is "unknown" unless a source says otherwise; a wall pin keeps its OSM/city/report source and confirmation.
- **Seeds keep their names** (`manual_walls.csv`, `osm_wall_overrides.csv`); only the models downstream change.

## Plan (separate PRs, each green on `dbt build` and `ci/check_export_fresh.py`)
1. Data: `venue_kind`, wall pins into `dim_venue`/`bridge_venue_sport`, fold `int_wall_venue_link` into the venue model; keep `walls` in the export for one release.
2. Export + docs: `export_app_data.py`, `app/data-dictionary.md`, `app/llms.txt`, changes feed (a wall appearing is a `venue_new` row).
3. App: one pin layer with a kind style, the hitting-alone filter, remove the wall layer, `WALL_SPORT` special cases and the "Hitting walls you can use alone" section; "Find by court" needs no wall branch.
4. Drop the old `walls` export key and models.

## Consequences
- Fewer special cases; new wall sports and states (OR, WA) need no extra code.
- Venue counts and some sport totals rise (about 440 walls today). Anything that quotes them (README, coverage snapshot, scorecard, Elementary tests, `ci/check_export_fresh.py`) must be re-baselined in step 1.
- Venue ids for walls must stay stable (the changes feed depends on it); wall keys become the id seed, so check the one-drift tolerance before step 2.
- Risk: wall-only pins crowd the zoomed-out map. Cluster or style by kind in step 3.

## Open
- Does a lone wall in a park with no listed venue need a park-level venue instead of its own? Today's name/distance link answers this for walls near a venue; the rest become their own venue.
- Public-only rule for Knuckle Racket moves from code to the sport mapping seed.
