# 0020. Pro Sunball: play at any beach or sand volleyball court (no pins)

Date: 2026-10-19. Status: accepted (2026-10-19), amended the same day (owner). Related: ADR 0002 (OSM first), 0007
(confirmation levels), 0015 (mission: discover sports beyond pickleball).

## Context
Pro Sunball is on the master sheet (2-4 players, felt rubber ball) but has no venues: no OSM tag exists, no club directory
was found (`docs/sport_directories.md`), and the sheet row has no court size, net height or rules link. Its surface is
"Various". Beach and sand volleyball courts are plentiful, so they are the obvious places to play it.

A scan on 2026-10-19 (`ingestion/extract_osm_beach_volleyball.py`, kept for reference) found 1,527 sand volleyball court
elements in CA + NV, about 841 sites (787 CA, 54 NV): 669 single-court sites, 42 named, 46 `access=private`.

## Decision
1. **Play anywhere, no pins.** The first version of this ADR proposed an inferred pin layer for those 841 sites. The owner
   chose the simpler model: Pro Sunball is treated like Frescoball, Smashball and Crossminton. It is a "play anywhere" sport
   (`sport_play_anywhere.csv`: "any beach or sand volleyball court"). It appears in the sport dropdown with that note and
   gets no pins of its own. Reason: the sport needs no fixed court, and ~800 pins would overclaim places nobody has
   reported using, and would make the sport look like it has venues.
2. **Honest wording.** The note says no official Pro Sunball courts exist and attributes the statement to the owner
   (2026-10-19). It does not say any specific court allows it or fits it.
3. **Scan is research, not a data source.** `data/raw/osm_beach_volleyball.csv` is not loaded into dbt. If the beta shows
   people want to find sand courts, a candidate layer (always `confirmation = inferred`, `access=private` and indoor dropped,
   no inferred streets for home-like places, shown only when the sport is selected) can be built from it with a new ADR.
4. **Promotion.** A real Pro Sunball venue (a club or event with a public page) goes in `manual_venues.csv` with `evidence`.

## Consequences
Costs one seed row, gives Pro Sunball a visible, honest entry in the dropdown, and keeps the map free of guessed pins. We
do not help players find a sand court from the map, and it does not say whether a given court allows the game.
