# 0022. Watch events: on-site vs screening, using the format values we already have

Date: 2026-10-23. Status: proposed. Builds ADR 0006 (watch events) and ADR 0021 (Watch & Social view); same link-out rules as ADR 0009 and 0012.

## Context
CLAUDE.md's "After beta" list says: split watch events into on-site vs `screening` (watch parties, dome screenings such as Cosm, broadcast-only), with a new `watch_format` value, an accepted_values test and a popup label.
Read 2026-10-23, part of that is already built (ADR 0006):
- `transform/seeds/watch_events.csv` already has `watch_format`, and `transform/models/schema.yml` already has the accepted_values test with six values: `in_person_ticketed`, `in_person_free`, `in_person_unconfirmed`, `watch_party`, `dome_screening`, `broadcast_only`.
- `FORMAT` in `app/index.html` already labels all six ("Watch party", "Dome screening", "Broadcast only"), and the popup shows the label as a badge.
- All 80 rows today are `in_person_*` (75 unconfirmed, 5 ticketed). No `watch_party`, `dome_screening` or `broadcast_only` row exists.
- Cosm Los Angeles (Inglewood) is the only Cosm in CA/NV. Its events page listed no racket sport on 2026-10-15; lead `cosm-los-angeles` stays open for US Open / Australian Open screenings. The Sphere (Las Vegas) listed none either.
What is missing is not a column or a test. It is (a) a plain statement that a screening is not played at the venue, and (b) a rule for when such a row may be added.

## Decision
Recommended: **keep the six existing values; do not add a seventh `screening` value. Treat `watch_party`, `dome_screening` and `broadcast_only` as the "screening" group, and say so in the popup.**

- **Group, not a new value.** "On-site" = the three `in_person_*` values (the sport is played at the pin). "Screening" = `watch_party`, `dome_screening` (the match is shown on a screen at the pin; the sport is not played there). The app derives the group from `watch_format`; the seed keeps the specific value because "Dome screening" and "Watch party" tell people different things.
- **Popup label.** Screening rows keep their badge ("Watch party" / "Dome screening") and the popup adds one line: "Shown on a screen here; not played at this venue." Header text and sort order are unchanged. No new filter or toggle in v1; add one only if the beta shows people confuse the two (`docs/feedback_findings.md`).
- **`broadcast_only` gets no pin.** It has no place, and the map is for places. The value stays valid for the seed but a row that has only a broadcaster is not added. (The existing coordinate test would reject it anyway.)
- **Tests.** The accepted_values test stays as is. Add one singular test in `assert_watch_events_valid.sql`: a `watch_party` / `dome_screening` row needs `info_url` (the venue's or broadcaster's own listing), `ticket_info` that says what is shown, and `source_note` that names the page read. Coordinates are the screening venue's.
- **How a Cosm-style event is added.** Only when a public page lists it with a date: the venue's own events page (cosm.com/los-angeles/events, read in the browser pane, since a plain fetch returns nothing), the organizer's page or one public Instagram/Meetup page (ADR 0009, 0012). One row per event: `sport` as listed, `level` from the event (a Grand Slam final is `pro`), `venue_name` = the screening venue, `watch_format` = `dome_screening` or `watch_party`, `date_status` = `confirmed` only if the page states the date, `tickets_url` only if the page sells tickets. The tournament-refresh task (`docs/tournament_refresh.md`, dome screenings row) already checks Cosm; it opens a PR, and a person merges (ADR 0019 stage 0). New-source rule: a screening venue the refresh has not read before is R3 (owner decides).
- **Honesty rules.** https links only (already tested). Public pages only, no logins (ADR 0007). Never guess that a bar or venue "usually shows" matches: a row needs a dated listing. If a listing says "showing the final" without a start time, the row says "time not listed". Anything not stated on the page is blank or labelled inferred, not filled in. CourtConnect links out; it sells no tickets and takes no bookings.
- **Out of scope.** The "Pro events" / "Amateur events" header rename (CLAUDE.md, separate item) and sports bars with no dated listing.

## Alternatives considered
- **Do nothing.** The values and labels exist, so the app is already honest about a screening if one is ever added. Cost of waiting: the popup would still not say "not played here", and nothing records the rule for adding Cosm rows. Rejected only because the fix is a few lines and a test.
- **New `screening` value** (the CLAUDE.md wording). It overlaps `watch_party` and `dome_screening` and loses the distinction between a bar watch party and a ticketed dome show. Rejected: the group is derivable.
- **New seed (`screening_events.csv`).** Duplicates every column, tests, staging and mart model and the export, for zero rows today. Rejected.
- **Separate map layer / toggle.** Right if screenings grow past a handful and users want them hidden. With zero rows today it is guesswork; revisit with beta findings.

## Consequences
- No seed, model or schema change for the group; one small singular-test addition and one popup line in `app/index.html` (a later PR, not this one; this ADR changes docs only).
- Cosm and watch-party rows can be added as soon as a dated public listing exists, with the same evidence rules as other watch rows (`verified_on` + `source_note`, 35-day freshness SLA).
- Risk: a screening pin looks like a place to play. Mitigated by the popup line and the badge; checked in the beta round.
- CLAUDE.md "After beta" line should become: "Watch events, screenings (ADR 0022, proposed): keep the six `watch_format` values, popup line 'Shown on a screen here; not played at this venue', one test for screening rows; then add Cosm LA rows only when a dated public listing exists."
