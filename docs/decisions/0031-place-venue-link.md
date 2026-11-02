# 0031. Hand-checked links from an Overture place to an OSM court group

Date: 2026-11-02. Status: accepted (owner, chat 2026-11-02; it adds a matching rule).

## Context
`int_place_venue_match` links an Overture place to an OSM court group by distance (100 m), same name (300 m), park or street-address match (300 m) or the inside-the-footprint rule (350 m). Peninsula Tennis Club is one club, but Overture pins it at 2525 Bacon St (the City of San Diego's address for Robb Field Athletic Area) while its 12 courts are mapped in OSM 430 m east, inside the same park. No rule reaches that far, so after ADR 0030 freed the courts from Barnes the club still showed as two pins: one at the courts with 12 courts and one at the address with none.

## Decision
- New seed `place_venue_link.csv` (`place_id`, `court_id`, `evidence`, `verified_on`). `int_place_venue_match` applies a row first (`match_rule = 'seed_link'`): the place joins the venue of that court's group. `court_id` can be any court of the group (OSM ids are stable).
- One row today: the Overture Peninsula Tennis Club place -> Robb Field court `way/1423812014`.
- Rows need evidence that both are the same facility (same name or operator, address or own-site text). A person adds them; an agent only with owner approval.
- No radius changes and no change for any place not listed.

## Alternatives
- Raise the place-match radii: changes every place in the state; the gold set (`make eval-match`) would need re-measuring.
- `closed_places.csv`: wrong, the club is open; only its pin is off.
- Move or re-geocode the Overture pin: we do not edit Overture data (ADR 0005).

## Consequences
- One Peninsula Tennis Club pin at the courts, source "both", address 2525 Bacon St (the park's address, as Overture gives it), 12 tennis courts.
- The pin takes the court location, not the address location. Anyone navigating by the address reaches the park entrance, about 430 m from the courts.
- Re-run `make eval-match` after the next OSM refresh; one row, so no change elsewhere is expected.
