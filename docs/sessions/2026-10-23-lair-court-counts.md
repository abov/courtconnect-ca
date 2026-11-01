# 2026-10-23 Lair of the Golden Bear: two camps, real counts

- The two Pinecrest pins are now "Lair of the Golden Bear: Camp Gold" (2 tennis, 1 pickleball) and "...: Camp Blue" (2 tennis, 4 pickleball), from the owner's count on satellite imagery; labelled Reported. New seed `venue_court_counts.csv` (replaces an OSM count for a sport the venue already has; derived sports like Frescotennis follow) plus two `manual_venues.csv` rows for the pickleball courts and names.
- Scan: 136 same-name + same-city groups (322 venues, 127 CA, 9 NV); 98 are inferred names from an enclosing campus, golf or country club (several court clusters share the park's name), 28 are chains (LA Fitness), so most are not duplicates. The 150 m duplicate guard does not catch them.
- Next: owner decides how to tell the 98 inferred-name groups apart (auto compass/court-count suffix vs imagery-based rows like this one); NV has 9 groups.
