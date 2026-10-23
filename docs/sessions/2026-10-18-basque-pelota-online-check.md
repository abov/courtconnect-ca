# 2026-10-18: Basque Pelota pins checked from public online sources

Owner decision (2026-10-18): no direct or in-person confirmation; public online sources only. No Yelp or Reddit page for these courts turned up in search; the usable sources are Euskal Kazeta / Euskal Kultura (Basque community press), a Funcheap listing, the LA Times (via Euskal Kultura) and club/venue sites. Main source: Euskal Kazeta court list, https://euskalkazeta.com/handball-courts-in-the-united-states/ (2024-10-14). Seeds: four new rows in `manual_venues.csv` (`confirmation=reported`, 2026-10-18), no pin removed. The pins still show as inferred in `mart_venue_confidence`, same as Kern.

| Pin | Finding | Seed |
|---|---|---|
| Kern County Basque Club (Bakersfield) | Already confirmed 2026-10-15 (club history page). The 2024 list says club members use the court; pros are invited each Memorial Day weekend. | unchanged |
| Centro Basco (Chino) | Court exists and is used: list says left-wall court, open to the public, since 1950; Euskal Kazeta 2026-06-30 schedules pilota finals/exhibitions there 2026-07-03/04; LA Times 2020 mentions impromptu games. Restaurant site (centrobasco.net) never mentions it, no open-play hours. | `centro-basco-chino`, access `club` |
| Aphessetche Trinquet (Chino) | Court exists (list: private, on the owner's dairy property, enclosed four-wall, games organised by the Chino Basque Club). Not a public venue. | `aphessetche-trinquet-chino`, access `private` |
| Basque Cultural Center (South SF) | Court in regular use (list); anniversary festival 2026-02-14 had free live pilota (Funcheap); 2014 youth pala program. List says available to club members. No current open-play schedule found. | `basque-cultural-center-south-sf`, access `club` |
| Hicks Canyon Elementary (Irvine, 6 ways) | No public source mentions a fronton or handball wall; OSM ways are asphalt pitches on a school playground, probably schoolyard wall-ball. Not rejected: no positive evidence either way. | none, stays inferred (low) |
| Paakuma K-8 School (San Bernardino, 2 ways, one access=private) | Same: no public source; only basketball courts and sports fields are documented (CEQA notices). | none, stays inferred (low) |
| Nunez Park (San Bernardino) | Already rejected 2026-10-15 (city page lists racquetball). | unchanged |
| Rejected Overture place `c5786a81...` | Already a reject. | unchanged |

New pin: **Elko City Park fronton (NV)**, not in OSM as pelota. List and basqueheritage.com: built 1975, only active pelota court in Nevada, municipal land, used at the National Basque Festival. Added as a Basque Pelota row on the existing "Main City Park" pin (within 150 m of 1515 E Idaho St); access `unknown`. The pin name stays "Main City Park" (a manual row with another name would rename the whole park pin).

Not added: the Bidart family backyard fronton in Chino (private home; Euskal Kazeta 2011), inactive courts (Fresno Basque Hotel, Stockton Hotel Central, etc.).

Next: schools need imagery or a visit report to reject; the Basque club sites (Chino Basque Club, Basque Cultural Center) have no public open-play schedule to link; recheck with the 2027 festival calendars.
