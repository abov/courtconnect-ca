# Contributing to CourtConnect CalNeva

Thank you for helping. CourtConnect is a map that links out to venues; it takes no bookings or payments. Honesty matters more than
polish: label what is guessed, and only mark something confirmed when you can show how you know.

## Ways to help
1. **Report a venue** (no code needed): open an issue with the "Report a venue" form. A reviewer turns it into a lead.
2. **Confirm a venue** (no code needed): open an issue with the "Confirm a venue" form to say you visited it, or to point to the
   operator's own page.
3. **Suggest a change** on the map: the "Suggest a change to this venue" link in a venue popup opens a prefilled form; a reviewer
   approves it and a pull request is opened for you. Pick **Report a racket sport played here** to pass on what you saw or were told
   (no link needed): it shows on the map as "Reported, not independently confirmed" until more people or an official page back it.
4. **Edit the data** with a pull request (below). Approved reviewers merge.

## Editing data
Data lives in CSV seeds in `transform/seeds/`. Edit these, never the files noted as generated:
- `manual_venues.csv`: venues no dataset knows. Set `confirmation` to `visited`, `official` or `reported`, with `confirmed_on` and `evidence`.
- `venue_actions.csv`: link-outs (booking, open play, classes). Keep `verified_on` and `evidence`.
- `venue_leads.csv`: claims not yet placed or checked. Leads are not shown on the map.
- `watch_events.csv` (https links only), `place_sport_overrides.csv`, `sport_aliases.csv`.

Do not edit `transform/seeds/all_racquet.csv`; it is overwritten from the Google Sheet.

Then run `make build` (needs Python, dbt and DuckDB; see the README) and include the result in your pull request.

## Rules
- Public pages and what you saw yourself only. Never use or share anyone's logins (Playtomic, PlayByPoint, Padel Up and similar), and
  never read logged-in pages.
- Do not use Google Maps or Google Places data (its terms forbid storing it). OpenStreetMap and Overture are fine.
- Do not copy text, reviews or photos from Yelp, Reddit or similar. Record the link in `source_url` and write your own summary.
- No personal information: no names or phone numbers of individuals.
- Every confirmation needs a date and evidence a reviewer can check. If you cannot confirm it, submit it as `reported` or as a lead.
- Keep changes small: one venue or one batch of related rows per pull request.

See [ADR 0007](docs/decisions/0007-confirmation-levels-and-leads.md) and [ADR 0008](docs/decisions/0008-contributors-and-confirmation-workflow.md).
By contributing you agree your contribution is released under the [MIT license](LICENSE).
