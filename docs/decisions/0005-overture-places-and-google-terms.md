# ADR 0005: Overture Maps as the second source; Google Places only as place IDs

**Status:** accepted (Overture built; the Google place-ID layer is built behind a dry-run switch and not yet run)

## Context
OpenStreetMap finds courts but not businesses: no clubs, indoor facilities, websites or phone numbers, and it knows nothing
about most of the 75 sports. We wanted a second source covering "all sports". The first idea was Google Places.

## The Google Places problem
Google's Places API policy says you must not "pre-fetch, cache, or store Places API content beyond the allowed exceptions".
The one thing the policy exempts is the **place ID**, which can be stored indefinitely. Names, addresses, coordinates, phone
numbers, websites and opening hours are governed by the Maps Service Terms and may not be warehoused. A Snowflake table of
Places results, published in a public repo, is exactly what those terms are written to prevent. It would also cost money per search.

## Decision
1. **Overture Maps places is the second warehouse source.** It is open data (CDLA-Permissive-2.0, Apache-2.0, CC0), so it can be
   stored and republished with attribution (`NOTICE.md`). It is published as GeoParquet on S3; DuckDB reads only the slices it needs.
2. **Google Places is used for place IDs only** (compliant): resolve a venue to a Google place ID, store the ID, and let the app fetch
   details live at display time. Needs the owner's own API key and billing. See `ingestion/google_place_ids.py` (dry-run by default).
3. **Evidence is graded.** A place counts toward a sport only on *strong* evidence: Overture's own racket category, or a distinctive
   sport word in its name ("padel", "squash", "table tennis"...). Ambiguous words ("Real Tennis" also matches *Camino Real Tennis Center*;
   "Beach Tennis" matches *Pacific Beach Tennis Club*) are *weak*: never counted as a venue, listed in `mart_places_to_review`, and a
   human can confirm or reject each in `transform/seeds/place_sport_overrides.csv`. The longest matching phrase wins, so "Table Tennis
   Association" is Table Tennis and not also plain Tennis.
4. **Places join venues by distance.** A place within 100 m of an OSM court belongs to that venue (average 30 m, 90% within 67 m);
   otherwise it becomes a venue of its own (`venue_source = 'places_only'`).

## Result (California, Overture release 2026-09-23.1)
| | OSM only (ADR 0004) | OSM + Overture |
|---|---|---|
| Venues | 9,490 | 9,925 (435 from places only) |
| Venues with a name | 3,787 | 4,343 |
| Venues with a **confirmed** name | 249 | 1,112 |
| Table Tennis / Badminton / Racquetball venues | 79 / 52 / 7 | 131 / 97 / 21 |
| Sports with a confirmed venue | 9 | 9 (5 more have weak matches awaiting review) |

Identical results on DuckDB and Snowflake, checked row by row.

## Known gaps
- **This did not solve the niche sports.** Business names mention only 12 of 75 sports. 51 still have nothing in either source:
  these are mostly informal games with no clubs. Realistic sources are governing-body and club directories, and community
  groups, not a places dataset.
- Overture categories exist only for tennis, pickleball, badminton, racquetball, squash and table tennis. Padel, beach tennis and
  others are found by name only.
- Overture confidence varies (0.25 to 1.0); venue names use only places with confidence of 0.5 or more.
