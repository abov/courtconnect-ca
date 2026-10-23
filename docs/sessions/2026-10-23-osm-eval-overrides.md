# 2026-10-23 OSM refresh, gold set, override cleanup

- Owner OK'd an OSM-only re-extract (CA+NV courts and parents; Overture places/addresses not re-run). Gold set after it: 129 pairs, 0 wrong merges, 4 missed (unchanged: Stanford West Campus, La Costa, Quail Lakes, Olympic Training Center).
- Live OSM check of the 144 override objects: only Jim Gilliam ways 1562970254/5 were fixed (now `paddle_tennis;pop_tennis`, 2026-10-15). Their 2 rows are dropped; the pin is unchanged. The ways no longer carry `leisure=pitch`, so the extract skips them; a mapper could restore it.
- Venues 10,267 -> 10,277 from normal OSM drift (23 moved/retagged, 33 new, 17 changed); `venues.json` re-exported. Next: `reverse_geocode_blanks.py` (+ `city-boundaries` if new cityless pins) per CLAUDE.md item 2.
