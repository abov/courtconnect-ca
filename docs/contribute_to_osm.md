# Improving the map by fixing OpenStreetMap

Most CourtConnect venues come from OpenStreetMap (OSM). If a court is missing or wrong here, fix it at the source and the next
data refresh picks it up. Rules are in [ADR 0011](decisions/0011-openstreetmap-contribution.md).

## How
1. Open a venue on the map and click "Fix or improve this on OpenStreetMap" (OSM-sourced venues only). The OSM editor opens at the venue.
2. Sign in with your own free OSM account (CourtConnect never logs in for you).
3. Add or fix tags, write a short changeset comment, save.

## Tags that matter to us
| Tag | Why |
|---|---|
| `leisure=pitch` or `leisure=sports_centre` | marks a court or a facility |
| `sport=*` (e.g. `tennis`, `pickleball`, `padel`, `beach_tennis`, `squash`) | decides which sport filters find it |
| `access=*` (`yes`, `customers`, `private`, `members`) | drives the Public / Private-members filter |
| `lit=yes/no`, `surface=*`, `covered=*` / `indoor=*` | lights, surface, indoor/outdoor |
| `name`, `operator`, `website`, `opening_hours`, `fee` | name quality and link-outs |

## Known gaps
- Unmapped padel and pickleball courts (many are tagged only as tennis).
- Courts with `access=private` that are really residential or club courts: only change this if you know.
- Unmapped tennis courts at Manhattan Country Club (Parkview Ave / Village Dr, 18 courts): our location there is INFERRED, so verify on the ground first.

## Don't
- Add anything marked inferred on our map, or guesses.
- Copy data from Google, Overture or other sites (licence conflict, ADR 0005).
- Do bulk or automated edits.
