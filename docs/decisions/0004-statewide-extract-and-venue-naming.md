# ADR 0004: Statewide extract, surface/setting data, and naming venues from the places they sit in

**Status:** accepted; names are approximate, surfaces and indoor/outdoor are sparse

## Context
ADR 0003 grouped courts into venues but 98% of them had no name, and the extract covered only Los Angeles.
The goal is courts for every racket sport, with surface (hard, clay, grass, sand), indoor/outdoor, and a name a player recognises.

## Decisions
1. **Statewide, in tiles, clipped locally.** California is fetched in 30 bounding-box tiles and clipped to the real state
   border (OSM relation 165475, via shapely). We do **not** use Overpass `area` filters: one public mirror silently returned
   zero rows for them, which would have produced an empty dataset with no error. Tiles that time out are split into
   quarters and retried; any tile that still fails makes the run exit non-zero.
2. **Name venues in order of trust:** a name tagged on the court > its operator > the smallest enclosing named park, school,
   club or sports centre (matched by bounding box) > unnamed. Golf courses, resorts and hotels are used only as a last resort,
   because their bounding boxes swallow neighbouring courts (a Stanford court was first named "Stanford University Golf Course").
   Every venue records `name_source`, so the app and the coverage report can tell a confirmed name from an inferred one.
3. **Be honest about what is assumed.** An untagged outdoor pitch is `likely_outdoor`, not `outdoor`. Unknown surface stays `unknown`.
4. **Only racket sports are kept.** A record is kept only if its sport tag maps to a sport on the master sheet. Tetherball
   (about 1,500 poles in California, all tagged `tetherball`) is hand-played, so it is excluded rather than counted as "Totem Tennis".

## Result (statewide, 2026-10-09)
| | Before (LA only) | After (California) |
|---|---|---|
| Court / facility records | 3,253 | 25,971 |
| Venues | 1,354 | 9,490 |
| Venues with any name | 23 (1.7%) | 3,787 (40%) |
| Venues with a **confirmed** name | 23 | 249 |

Identical results on DuckDB and Snowflake. Pickleball: 940 venues / 3,278 courts. Tennis: 8,946 venues / 22,121 courts.

## Known gaps
- 53 of 75 sports have no OpenStreetMap tag; 13 more are tagged but have no California courts mapped. See `docs/coverage_snapshot.md`.
- About 90% of courts have no surface tag; indoor courts and beach/sand courts are barely mapped.
- Bounding boxes over-cover irregular shapes, so some inferred names will be wrong. A polygon join would fix this but needs full geometries (much larger downloads).

## Next
A second source (Google Places keyword search per sport plus the alias table, and club / league directories) for the 53 untagged sports, surfaces,
indoor courts and confirmed names. Then compare Places names against the inferred ones to measure how often the inference is right.
