# OSM fix list (2026-10-22)

Ready-to-act list of OpenStreetMap (OSM) objects whose tags our own research found wrong or missing. Built only from what the repo already records (`transform/seeds/osm_court_sport_overrides.csv`, `venue_leads.csv`, `manual_venues.csv`, `docs/padel_scan.md`, session notes); nothing new was researched and nothing was edited in OSM. Object ids and current tags checked against our raw extract of 2026-10-09 (Las Vegas ways 2026-10-14). Rules for editing: [ADR 0011](decisions/0011-openstreetmap-contribution.md), [contribute_to_osm.md](contribute_to_osm.md): a person edits with their own OSM account, no bulk or automated edits, nothing marked inferred, nothing copied from Google/Overture.

Why bother: each fix lets us drop an override row, so the next extract is right by itself. After a fix lands, re-extract, then delete the matching `osm_court_sport_overrides.csv` rows.

**Evidence strength.** "Owner" = the project owner's report (not a public page; the mapper should still check the ground or imagery). "Imagery" = our Esri World Imagery measurement (a hint, not proof; OSM's own rule is not to retag from imagery alone where a survey is possible). A public URL is given where one exists. Links: `https://www.openstreetmap.org/way/<id>`.

## A. Wrong sport tag, correct value known (act first)

| OSM objects | Now | Should be | Evidence |
|---|---|---|---|
| way 1563332703 (El Segundo Rec Park), 547304223 (Westchester Enriched Science Magnets) | `sport=padel` | `sport=paddle_tennis` | Owner 2026-10-10: no padel courts, they are paddle tennis. Same editor and aerial batch (changeset 189701018, 2026-09-28) as the Santa Monica ways below |
| ways 1562970254, 1562970255 (Jim Gilliam Rec Center) | `sport=padel` | `sport=paddle_tennis` | Owner, issue #99, 2026-10-14: these 2 are pop tennis courts |
| ways 1562971116-1562971119 (Fox Hills Park) | `sport=padel` | `sport=paddle_tennis` (likely) | Owner 2026-10-10: no padel; tag "likely paddle tennis" |
| ways 712564135, 712564138, 712564140, 712564142, 712564144, 712564146, 712564148, 712564150, 712564196, 712564198, 712564200 (Venice Beach, 11 courts) | `sport=tennis` | `sport=paddle_tennis` | Owner 2026-10-14: pop tennis only, no other sport may be played here |
| ways 1420899232, 1420899233 (Van Nuys Sherman Oaks, small courts east of the tennis courts) | `sport=pickleball` | `sport=paddle_tennis` | Owner 2026-10-18; Esri z20 2026-10-18 measures 6.3 x 14.2 m (21 x 47 ft), service lines 12 ft from net = paddle tennis; City of LA fee table lists "Paddle Tennis/Pickleball Court" (recreation.parks.lacity.gov/sports/tennis/facility/van-nuys-SO) |

## B. Wrong sport tag, remove it (correct value unknown or only inferred)

Do not write the "likely" value unless the mapper can see the court.

| OSM objects | Now | Fix | Evidence |
|---|---|---|---|
| ways 1420731936 (court by Fox Hills Park, Culver City), 1562972034 (Mindanao Way, Del Rey) | `sport=padel` | remove `padel`; Mindanao may be paddle tennis, **unconfirmed** | Owner 2026-10-10 (no padel). Mindanao: LA Rec and Parks lists "Paddle Tennis" at Bill Rosendahl Del Rey Park (recreation.parks.lacity.gov/park/bill-rosendahl-del-rey, 2026-10-18) with no count or location; needs a visit |
| ways 1563328063-1563328068 (Santa Monica Beach Club, 201 Palisades Beach Rd) | `sport=padel` on all 6 | at most 1 padel (enclosed); the rest `paddle_tennis`; **needs lookup of which way is which** | padelbrowser.com/padel-courts/the-beach-club (viewed 2026-10-17): 1 enclosed padel + 5 paddle tennis. Lead `santa-monica-beach-club-padel` waits on the club's own page |
| way 1563338379 (Calabasas) | `sport=padel` | remove `padel` | Same editor/batch family (changeset 189702848, 2026-09-29); no public page lists padel there (2026-10-17) |
| ways 1420709156-1420709161 (San Juan Union School) | `sport=padel` | `pickleball` | Benito Link, benitolink.com/?p=19755: converted tennis courts are pickleball (2026-10-17); imagery agrees |
| ways 1420187682-1420187685 (Normandale Dr, Lake Forest), 1420188422-1420188424 (Orangetree Park, Irvine) | `sport=padel` | remove `padel`; imagery says pickleball size (inferred) | No public page lists padel (City of Irvine for Orangetree), imagery 2026-10-17 |
| ways 1420723587, 1420723588 (Silver Creek Valley CC) | `sport=padel` | remove `padel`; club lists tennis + pickleball | Club tennis page (2026-10-17); imagery |
| ways 1237161317, 1237161318 (iTennis La Habra) | `sport=padel` | remove `padel`; club offers tennis + pickleball | lahabra.i-tennis.com (2026-10-17); 2024 aerial tag |
| ways 1481104355-1481104358 (Bakersfield Country Club) | `sport=padel` | remove `padel`; imagery shows pickleball-size courts (inferred) | Esri 2025-09-09, viewed 2026-10-17. Re-add padel only from a club page |
| way 1065709237 (Balboa Park Tennis Club) | `sport=padel` | remove `padel` (tennis) | balboatennis.com lists 25 lit hard tennis courts only (2026-10-17) |
| way 1169422000 (West Valley College) | `sport=padel` | remove `padel` (tennis) | College athletics tennis page: 16 hard tennis courts (2026-10-17) |
| way 1423690681 (Reagan Education Centre, Clovis) | `sport=padel` | remove: no court visible | Esri 2026-03-03, grass field (2026-10-17) |
| ways 562935627 (Residence Inn San Ramon), 391797146 (Wildhorse, Davis), 1056307083 (Tracy), 616168506 (Vacaville), 462636882 (Granite Bay), 965287673 (San Jose), 1302182230 (Saratoga) | `sport=padel` | remove `padel`: courts too small or absent for padel (about 7 x 13 m to 15 x 9 m; none at Granite Bay) | Esri imagery measured 2026-10-17 (dates in the seed reasons). Several are private backyards: leave the objects, just fix the tag |
| ways 37014242, 1164879396 (Washington Park, Alameda) | `sport=paddle_tennis` | `tennis` (inferred) | City of Alameda Rec and Parks lists tennis courts there, no paddle tennis; imagery 2026-03-24 shows tennis-style courts with service boxes (2026-10-17) |
| ways 1148106652 (Exeter City Athletic Park), 1447525570-1447525573 (Frank F. Garside Jr High, Las Vegas) | `sport=paddle_tennis` | remove; Exeter's extra way is not a ninth court (8 tennis already mapped); Garside is bare asphalt | Owner checked Google Maps 2026-10-17 (Exeter); Esri 2025-09-12 (Garside) |
| ways 1262737425 (Ditch Rd, Simi Valley), 1291530436 (Canyon View Trail, Simi Valley) | `sport=paddle_tennis` | **unresolved**: Ditch Rd is a private residential court (sport not settled), Canyon View is unreadable on imagery | Esri 2025-12-11, 2026-10-17; low priority, leave unless a local can look |
| way 1432707080 (Lair of the Golden Bear camp) | `sport=paddle_tennis` | remove; camp offers pickleball and tennis | alumni.berkeley.edu/camp-at-the-lair/things-to-do/ (2026-10-15) |
| way 819411778 (Nunez Park, San Bernardino) | `sport=pelota` | probably `racquetball` (inferred) | City of San Bernardino facility page lists 2 outdoor racquetball courts + 1 tennis court: sanbernardino.gov/Facilities/Facility/Details/Nunez-Park-40 (2026-10-15) |
| ways 1030846409, 1030846411, 1030846413, 1030846415, 1030846417, 1030846419 (Hicks Canyon Elementary), 549195121, 549195123 (Paakuma K-8) | `sport=pelota` | **needs lookup**: outdoor asphalt pitches with a wall, not a fronton; best OSM tag for a school hitting wall is undecided | Owner decision 2026-10-21. Do not guess a tag; a local mapper should check |
| node 9112024493 (Marine Avenue Park, Manhattan Beach) | `sport=table_tennis` | tables closed and boarded up: mapper's call (OSM lifecycle prefix such as `disused:` is the usual way) | Owner, issue #112, 2026-10-15 |

## C. Wrong or missing access, name or sport (found in venue research)

| OSM objects | Problem | Fix | Evidence |
|---|---|---|---|
| ways 1466345853, 1466345856, 1466345860, 1466345865 (Big Canyon CC, Newport Beach, 4 pickleball) | `access=permissive` | `access=private` (or `members`); verify on site | Club site bigcanyoncc.org, Membership page, read 2026-10-16: "member-owned private club and membership is by invitation". Evidence is club-level, not court-level. Nearby tennis ways 1184097981-2 have no access tag |
| ways 259153846-259153855 and 796228303-796228310 (18 tennis courts, Parkview Ave / Village Dr, Manhattan Beach) | no `name`, `operator`, `access` | name/operator/`access=members` **only after** confirming on the ground that these are Manhattan Country Club's courts | Bay Clubs page bayclubs.com/manhattancc (16-18 tennis, 7 pickleball), read 2026-10-10 and 2026-10-18. Location is **inferred** here, so verify first (already in contribute_to_osm.md) |
| ways 442673332, 442673333 (Manhattan Heights Park, tennis) | pickleball not tagged | add `pickleball` (e.g. `sport=tennis;pickleball`) if the lines share these courts; **needs ground check** | Owner report 2026-10-15: at least 2 pickleball courts; not on a city page yet |
| Elko City Park fronton, 1515 E Idaho St, Elko NV (about 40.8419, -115.7531) | no pelota court mapped (only tennis ways 953838245-6, 1318152626-9 nearby) | **needs lookup**: add the fronton as `leisure=pitch` + a pelota `sport` tag | Euskal Kazeta list of US handball courts (euskalkazeta.com/handball-courts-in-the-united-states/, 2024-10-14): City Park Fronton, built 1975; basqueheritage.com (read 2026-10-18) |
| Van Nuys Sherman Oaks Park (14201 Huston St), single-wall handball court | not mapped | **needs lookup**: add a pitch, sport not known (imagery cannot say which wall sport) | Owner 2026-10-18; Esri z20 measures about 22 x 36 ft |

## D. Duplicate courts

OSM draws some courts twice (same sport, same spot): 55 pairs within 1.5 m found 2026-10-18 (e.g. Burroughs HS Burbank 16 drawn for 8, Delano Chavez HS, Valle Lindo Park, Van Nuys Sherman Oaks). Our `stg_osm_courts` keeps the lower id, so the map is right, but the duplicates still sit in OSM. **Needs lookup**: list the pairs from `data/raw/osm_courts.csv` (same `sport`, under 1.5 m) before anyone merges; one object of each pair should be deleted by a person.

## Already tracked elsewhere (not a tag fix)

- Unmapped padel and pickleball courts, and pickleball lines on tennis courts never tagged: general gap in contribute_to_osm.md; no specific objects.
- A generated list (`make osm-fixes`, ADR 0011 "consider later"): not built; this static doc stands in until contributors ask for more.
