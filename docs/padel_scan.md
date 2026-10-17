# Padel court check (plan, added 2026-10-17)

## Why
Padel and pop tennis (also called paddle tennis, `Pop Tennis` in the sheet) are two separate sports on two different courts, but the names get mixed up:
- **Padel**: enclosed court 20 x 10 m (65 x 32 ft) with glass and/or mesh walls that stay in play, turf surface, solid stringless racket, depressurised tennis ball. Sheet row `Padel`, FIP.
- **Pop tennis**: open court 50 x 20 ft (60 x 27 ft on the sheet) with a low net, no walls, concrete, solid paddle, felt rubber ball. Sheet row `Pop Tennis`, IPTA. Common in West LA / Southern California parks.
- **Platform tennis** is a third, separate sport (aluminium deck with wire screens, outdoors in winter). Do not merge it into either.

Known mix-ups already fixed one by one: 10 OSM courts tagged `sport=padel` that were pop tennis (El Segundo, Fox Hills, Mindanao Way, Jim Gilliam, Westchester; `osm_court_sport_overrides.csv`), a Padel pin on a Miami Beach club (`website_overrides`), and Overture category/name conflicts (`assert_category_sport_not_contradicted_by_name`). The cause is systemic (OSM taggers use `padel` or `paddle_tennis` loosely; "paddle" appears in both names), so check the whole set instead of waiting for reports.

## Reference sites (leads only)
Use these to find club names we may be missing; they are compiled directories, so treat each entry as a lead, not as evidence.
- https://www.padelcourtsfinder.com/
- https://padelusa.org/where-to-play/ (USPA)
- https://www.padelmapusa.com/

Rules: public pages only (ADR 0007); read each site's terms before copying anything beyond facts (venue name, city, number of courts, link); do not bulk-copy or scrape their lists; no Google Places data (ADR 0005). Confirm every venue on the club's own page or a public booking page (read as text, never the owner's logins) and keep `verified_on` + `evidence`. Add a row to `docs/sport_directories.md` for each site once its terms are read.

## Steps (cheapest first; one per session)
1. **Audit what we have.** List every venue with Padel in the export (`venues.json`/`dim_venue`) and every Pop Tennis venue; flag Padel rows that are OSM-only or Overture-only with no club page, and Padel rows whose name or park looks like a rec centre or school (likely pop tennis). Write the list to the session note; no seed changes yet.
2. **Fix the mix-ups.** For each flagged row: confirm on a public page, then reject Padel (and add Pop Tennis if the page says so) in `osm_court_sport_overrides.csv` / `place_sport_overrides.csv`, or confirm Padel in `place_sport_overrides.csv`. Run `dbt build --select` on the touched models first, full build once at the end.
3. **Add missing padel clubs.** One metro at a time (LA, San Diego, Bay Area, Las Vegas, Sacramento), compare the three reference sites against our list; for each club we lack, read its own page and add it to `manual_venues.csv` (court count in the evidence; indoor/outdoor if stated). Cheapest first: Los Angeles, then propose more.
4. **Guard rails.** Add a dbt test or a `ci/` check so a Padel row needs one of: OSM `sport=padel` on a court that also has `walls`/`glass` tags or a club name, an Overture place with "padel" in the name, or a confirmed override. OSM `paddle_tennis` stays `Pop Tennis` (`osm_sport_map.csv`); consider lowering `padel_tennis` from `high` to `medium` if the audit finds it is used for pop tennis. Optionally add "pop tennis" / "paddle tennis" / "padel" alias checks to `sport_aliases.csv` so a search for one never returns the other.
5. **Tell people the difference.** A one-line note in the sport "About" card (see `docs/sport_discovery_plan.md`) and in the suggest-a-change form: "Padel = walled glass court; pop tennis = open court with a low net". The blurb itself goes in the Google Sheet.
6. **OSM.** Where an OSM court is clearly pop tennis but tagged padel (or the reverse), fix it in OSM (`docs/contribute_to_osm.md`) so the next extract is right without an override.

## Done when
- Every Padel pin has a club page, a confirmed override, or is labelled inferred; no pop tennis court is shown as Padel (and the reverse).
- The padel count by metro is compared with the three reference sites and the gaps are either added or listed with a reason.
- A test fails when a Padel row has no supporting signal.
