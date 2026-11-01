# 2026-10-18 Pop Tennis West LA map locations

- Compared the owner's Google My Map (Pop Tennis West LA) with the `pt-*` rows in `manual_venues.csv`. The owner confirmed the map's pins are the correct locations, so all 20 `pt-*` rows that exist on the map now use the map pin coordinates (taken from the map's embedded viewer data, not the KML export, which has no coordinates). Names, court counts, access and rules already matched and were not changed.
- Biggest fix: Elenda (was 2.1 km off, at 9070 W Venice Blvd; now at Culver Blvd & Elenda St). Shorecliff Golf Club moved ~880 m, Alondra ~570 m, Ladera Linda / Charles H. Wilson / Oberrieder ~470 m. Manhattan Heights Park and Jim Gilliam owner moves from 2026-10-14/15 were reset to the map pin by the owner's request.
- Not on the project: the 9 private homes (Chatsworth, Granada Hills), left out on purpose (privacy). South End Racquet Club keeps its own `southend-racquet-club` rows (club site, multi-sport).
- Next: pins that merge with an OSM court (Fox Hills, Charles H. Wilson, Jim Gilliam) still show the OSM court position, 150-170 m from the map pin.
