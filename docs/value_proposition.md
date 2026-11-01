# Value proposition and audiences (2026-10-23)

Status: **proposal, no code changed.** Sources: `docs/product_brief.md`, `docs/competitor_scan.md` (2026-10-16/21; re-check before quoting), ADR 0015. Purpose: decide what the page says about why it exists and who it is for, before more visual work. Parts 1 and 2 of the front-end plan (friendly/easy, professional look) then follow from it.

## Why this exists (one paragraph)

Court finders each cover one sport, or only places you can book. Racket players in California and Nevada also play on public park courts, hitting walls, rec centers and in sports most apps skip (padel, squash, badminton, table tennis, Pop Tennis, paddleball). CourtConnect is the one free map of all of them, honest about how sure it is, that also shows what to watch and who to play with.

## What other services do not do (our four differences)

Each is already true and backed by the competitor scan; the page should show them, not just claim them.

1. **Every racket sport, one map.** Pickleheads/Places2Play: pickleball. Playtomic: padel/tennis/pickleball clubs. Show it: the sport picker lists the lesser-known sports with a one-line About card.
2. **Every place, not only bookable ones.** Parks, walls, YMCAs and rec centers sit next to clubs. Show it: pins for free public courts are first-class, not hidden behind "book now".
3. **Honest labels.** Confirmed / official / reported with a date; inferred data says so (ADR 0007). Stale data is the known weakness of the directories. Show it: the trust chip and "verified on" date in every popup.
4. **Links out, never books or charges.** No account, no fees, no lock-in: a club's own booking page, league or Meetup is one tap away. Show it: link-outs stay the main button; footer line "We link out; we never take bookings or payments".

## Audiences and what each gets

| Audience | Their question | What they get today | Gap (proposal) |
|---|---|---|---|
| **Player** | "Where can I play, with whom?" | Map, filters, Play/Watch/Social, focus helpers | Say the four differences above on the front door in two lines |
| **Club or facility** | "Can people find us, and is it right?" | Free pin, honest label, link-out to their site, suggest-a-change form | A visible "Is this your club? Fix or add your listing" path (reuses the community form; no accounts) |
| **Company** (operators, organizers, brands, chains) | "Can our courts, leagues or events reach players?" | Events and link-outs we find ourselves | An "Add your event or league" path through the same form. Anything paid or promoted needs an ADR first (ADR 0015: no accounts or payments) |

Not promised: bookings, payments, accounts, rankings, paid placement. Clubs and companies cannot buy a better label; a label changes only with public evidence.

## Proposed page wording (draft, not built)

- Front door under the headline, two short lines: "Every racket sport, every kind of court, from free parks to private clubs." / "Labelled by how sure we are. We link out; we never take bookings or payments."
- Footer or About dialog: three short blocks, "For players", "For clubs", "For companies and organizers", each with one sentence and one button (Use the map / Fix or add your listing / Add an event).

## Measures (GoatCounter, already installed)

Share of visits that open a venue and that click a link-out (player value); number of club/organizer submissions through the form per month (club/company value). Baseline first; compare after the front-door lines ship.

## Decisions for the owner

1. Are the four differences the right ones, or is one missing (for example "free, no ads")?
2. Clubs and companies: is a "fix or add your listing/event" path enough for now, or is a paid or featured tier the real goal? (The second needs an ADR; the first needs only text and a button.)
3. Approve the draft wording, then it goes into the front-door PR with the visual polish.
