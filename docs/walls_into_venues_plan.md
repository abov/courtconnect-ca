# Plan: fold hitting walls into venues (scoping only, 2026-10-27)

**Why they are separate today.** Walls were added in #86 as solo-practice spots from OSM handball/wall tags plus `manual_walls.csv`. They got their own models (`dim_wall` -> `mart_wall_pins`), their own export key (`walls`), their own map layer (orange pins) and popup. Venues come from Overture/OSM places and courts matched in `int_place_venue_match`. Nothing in the product decided the split; it followed the data. Cost: a venue with a wall never lists the wall sport in its own popup, and wall sports need a separate sport->wall-type table in the app (`WALL_SPORT`).

**Size.** 448 wall pins (276 OSM-tagged, 140 inferred, 24 official, 8 reported) vs 10,277 venues; 406 are one-wall. Only 37 name a nearby venue (`near_venue_name`).

**Option A, link walls to the venue they are at (recommended first; one PR).**
- dbt: `int_wall_venue_link` joins a wall pin to a venue by `near_venue_name` or by distance (start at 150 m, check by hand against the 37).
- Export: venue gets `wl` (wall types + count + confidence). Popup "Plays:" adds "Hitting walls on site: 2 one-wall (reported)". Orange pins and walls-only filters stay.
- Walls do not count as courts, so venue counts and sport coverage numbers do not move.

**Option B, walls become venues (3 PRs, after the beta).** Wall sports go into `bridge_place_sport`, one pin layer, wall type becomes a court attribute, and the `walls` key, orange layer, legend, `wallNode` popup and `WALL_SPORT` map are retired.
- Risks: 416 tagged/inferred walls would sit among real venues (needs the inferred label and a "not checked" state in the main list); wall access vocabulary differs; `wall_count` per pin has no venue equivalent; venue totals, `make quality`, the match gold set, `app/llms.txt` and `data-dictionary.md` all change.

**Owner decisions needed before B:** do walls count in venue and coverage totals? Should unchecked OSM-tagged walls show in the main list at all?

**Next step if approved:** A only, in its own session.
