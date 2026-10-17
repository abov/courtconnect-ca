# 2026-10-17 padel / pop tennis audit (steps 1-2 of `docs/padel_scan.md`)

## What the audit found
Audited all 33 Padel and 27 Pop Tennis venues. Pulled each OSM tag's changeset from the public OSM API: most OSM `sport=padel` tags came from aerial-imagery passes, not surveys.
- **Unreliable batches.** MapRoulette "Tracing individual tennis courts" (user ujinevich, Aug 2025): 3 of 3 places we could check were wrong (San Juan School = pickleball, Silver Creek = tennis + pickleball, Culver City way/1420731936 = owner said no padel). Editor 0x4273's Sept 2026 "Separate pitch(es) from recreation ground(s)" batch: the owner already rejected El Segundo, Fox Hills, Mindanao, Westchester; Santa Monica Beach Club (6 ways) and Calabasas (1) are from the same batch.
- **Real padel confirmed:** LA Galaxy Park (4 Taktika courts, Business Wire 2023-02-22), Barnes Tennis Center (7 courts, Taktika), Padel Up Century City (own page: 2 outdoor rooftop courts, now a manual venue), plus the existing manual/override clubs.
- **Duplicate fixed:** Taktika Carson and LA Galaxy Park were two pins (same address 18400 Avalon Blvd, geocoded 330 m apart); manual pin moved onto the courts, so they now merge.

## Seed changes
- `osm_court_sport_overrides.csv`: 26 Padel rejects (San Juan School 6, Lake Forest 4, Orangetree Park 3, Silver Creek 2, iTennis La Habra 2, Balboa Park Tennis Club 1, West Valley College 1, Santa Monica Beach Club 6, Calabasas 1), each with reason. Padel venues 33 -> 24; map total 10,267 -> 10,264.
- `osm_sport_map.csv`: `padel` lowered from high to medium (unverified OSM padel tags now land in the review queue as `osm_tag_loose`); removed `padel_tennis` (not a real OSM value; owner 2026-10-17); the only valid keys are `padel`, `paddle_tennis`, `paddletennis`, `pop_tennis`, `poptennis`, so added `paddletennis`, `pop_tennis`, `poptennis` -> Pop Tennis (also in `ingestion/extract_osm_courts.py` and `build_osm_sport_map.py`, so the next extract fetches them) (the owner's own Jim Gilliam edit used `pop_tennis`, unmapped until now; adds Kahler Russell Park).
- `manual_venues.csv`: Padel Up (Century City) added; Taktika Carson pin moved.
- Evidence rule: nothing here cites Pickleheads/Bounce listings (terms; see memory). Several search results came from them as leads only.

## Imagery pass (added later 2026-10-17)
Viewed Esri World Imagery tiles (zoom 19, 0.08-0.5 m/px, captured 2024-11 to 2026-03; fetched to a scratch folder, deleted afterwards, nothing stored) at each unverified spot, with a true-scale 10x20 m padel outline drawn on it. Calibration: the LA Galaxy Park padel courts match that outline exactly. Size is the test, because glass walls are not visible from above and NAIP (0.6 m) is too coarse for this.
- **9 more Padel spots rejected (12 ways)**: Bakersfield CC (four pickleball-size courts; imagery 2025-09-09 predates the 2026-02 tag, so re-add if a club page shows padel), Reagan (grass field), Residence Inn San Ramon, Wildhorse (private backyard, not the golf club), Tracy, Vacaville, Granite Bay (no court visible), San Jose, Saratoga (all single backyard courts smaller than padel). Padel venues now 12 confirmed + 2 name-keyword only (below); every OSM-only Padel tag is gone. Map total 10,259.
- **Pop Tennis (OSM loose) left flagged, nothing rejected**: Alameda Washington Park and Exeter show tennis-style courts of unclear size; Garside (Las Vegas) and the two Simi Valley courts are too blurry or overgrown to read; Kahler Russell Park fits a pickleball/paddle-size court. These need a site visit, a city page or street-level photos.

## Still unverified (kept, labelled needs-review)
Padel San Diego (4606 Ingraham St) and San Diego NOX Padel Club (name_keyword only): the NOX pin is at 2015 Birch Rd, Chula Vista, the same address as ESL Padel (3 indoor courts, opened fall 2025, per directory + Playtomic snippets; club's own page could not be read), so likely real and renamed.

## Next (step 3 and 4)
- Read the Santa Monica Beach Club's own page (1 enclosed padel court + 5 paddle tennis per a directory) and add both sports.
- Missing padel clubs seen in directories (leads only, each needs its own page): San Diego (Kingdom of Padel, King of Padel, ESL Padel, Padel N9NE, Cali Padel Club, USD Club Padel), LA (Ballers DTLA, Bay Padel Marina del Rey, Chiquitas, Los Angeles Padel Club), Bay Area (Bay Padel San Jose / Sunnyvale / Dogpatch / Treasure Island, Oakland Padel), Taktika at University of the Pacific. Read each directory's terms and add a `docs/sport_directories.md` row first (padelusa.org/where-to-play now 404s; clubs live under padelusa.org/clubs/california/...).
- San Juan School has 6 free public pickleball courts (Benito Link): worth a manual venue now that the padel tag is rejected.
- dbt guard test (step 4) not added: with the confidence drop the ladder already flags the unverified rows.
