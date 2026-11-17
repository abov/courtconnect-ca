# ADR 0040: Open play is both a venue attribute and an event

Status: accepted (owner delegated the choice, 2026-11-16)

- A pin shows where a sport is playable. A place with no permanent courts (a gym set up for one night, e.g. Westchester Recreation Center badminton) still gets a pin, labelled so in `rules`, with an estimated court count marked as an estimate.
- Open play with a known schedule is a recurring row in `social_events.csv` (`kind=open_play`): it appears in the events view and on the pin.
- Open play with no known schedule stays a `venue_actions.csv` link-out ("Offers: Open play"), no event row.
- Rule: a schedule makes it an event; the venue always keeps its pin.
