# Product brief: what CourtConnect is, why each piece exists, and how to make the page clear (2026-10-22)

Status: **PR 1 and PR 2 built 2026-10-22 (mode names, promise headline, stats to footer, wall note collapsed, About card collapsed, "Filters (n)", short confirmation chip); PR 3 (welcome card) skipped by owner, legends merged into one "Map key" button in the list bar and "Share this place" built 2026-10-22; "This week" strip not built.** Source: `app/index.html` read as text, ADR 0015, `docs/ux_polish.md`, `docs/competitor_scan.md`, `app/data/venues.json` meta (generated 2026-10-22). Builds on, does not replace, the visual polish plan.

## 1. The one-sentence product

> **Find a place to play any racket sport in California and Nevada, see what is on, and find people to play with.**

Three verbs, from the mission (ADR 0015): **Find** (a court), **Watch** (a match or event), **Gather** (people to play with). "Try a new sport" is served by the sport picker and its About card (the separate "Try something new" card was dropped by the owner on 2026-10-21, so it is not proposed here).

Who it is for, in order of how many people they are:
1. **The player who wants a court now.** "Where can I play pickleball / tennis / padel near me?" This is 90% of first visits.
2. **The curious player.** "I heard of padel / squash / pickleball alternatives. Is there any near me?"
3. **The person who wants company.** "Who do I play with? Is there open play, a league, a group?"
4. **The spectator.** "Is there a tournament I can watch?"
5. **The contributor.** "This is wrong / missing, let me fix it." (Small, but it keeps the data alive.)

## 2. What exists today and why (the full breakdown)

Numbers are from the live export: **10,257 venues** (4,521 with a known name, 1,620 confirmed), **39 of 81 sports** with at least one venue, **80 watch events**, **21 social entries**, **927 hitting walls**, **276 link-outs** (leagues, clinics, open play, etc.), 10 player-finding platforms.

| Layer | What it is | Why it exists | Who it serves | Visible to visitor? |
|---|---|---|---|---|
| Venue map (OSM + Overture + hand-curated) | 10k pins across CA + NV | The core promise: "every place" (ADR 0015). Without it nothing else matters. | Player, curious | Yes, the map |
| Confirmation levels + "inferred" labels | Confirmed / listed business / guessed name / unnamed | Honesty rule (ADR 0007): never present a guess as fact. This is the trust differentiator against directory sites. | Everyone, silently | Yes, and too loudly (see §3) |
| Sport picker (81 sports) + About card | Pickleball is not the whole story | Sport discovery, tennis and lesser-known sports stay findable | Curious | Yes |
| Link-outs (`venue_actions`) | Website, leagues, clinics, open play, lessons | CourtConnect links out and takes no bookings or payments, so the *action* lives on the venue's page | Player | Yes, in the popup ("Join & follow") |
| Watch & Social view | Dated events (80) plus recurring groups (21) | Answers "what is on" and "who can I play with" without building accounts (social phase A, closed 2026-10-21) | Spectator, gatherer | Yes (mode button) |
| Player platforms + "Find people to play with" | 10 apps/groups linked per sport | Same, link-out only | Gatherer | Yes (note under the sport picker) |
| Hitting walls | 927 solo-practice spots | Underserved need, very few sources | Tennis/racquet players | Yes (only when a wall sport is picked) |
| Suggest a change / community form / OSM fix link | Three ways to correct data | Keeps data fresh without owner review; feeds the self-service goal (ADR 0008, 0011) | Contributor | Yes, tucked in popup details |
| "How complete is this data?" | Per-sport coverage table | Honesty about gaps | Skeptic, owner | Yes, in the footer |
| Pipeline, dbt tests, gold set, address fill, freshness SLA, quality scorecard | Everything under `ingestion/` and `transform/` | Makes the pins trustworthy and keeps them from rotting. It is the engine, not the product. | Nobody sees it | No |
| Scheduled agents / self-service plan | Refresh, triage, link watcher, reader | Long-term goal: runs itself with minimal human review (ADR 0015, 0019) | Owner | No |
| GoatCounter analytics | Anonymous counts | Lets the beta answer "do people actually use it?" (ADR 0013) | Owner | No |

**Why you keep going, in one line:** each layer removes one reason a player would give up. The map answers "is there a court", labels answer "can I trust it", link-outs answer "what do I do next", Watch & Social answers "what is on and who with", community reports answer "who keeps it right". The pipeline and agents exist so that does not depend on you doing it by hand forever.

**The honest product-management read:** most of the work so far (roughly 80%) is the invisible engine, and it is strong. The visible surface grew by accretion: each feature added a control to one side panel. The next best investment is not another data scan, it is making the front door legible. Items 5 and 6 of the roadmap (more facility scans, more coverage leads) can wait without hurting anyone.

## 3. Why the page feels "all over the place" (diagnosis)

Before a first-time visitor sees one court, the side panel shows roughly **20 things**: a stats headline, a tagline, two long mode buttons, a sport dropdown, up to three notes (people to play with, "anywhere" note, wall note), a search box, "Near me", "More filters" (three groups of chips), a sport-info disclosure, "Clear filters", a count, "Hide list", a ring key, then the list, then "Map key", a wall legend and the footer.

Four root causes:
1. **It is built from the data model outward, not from the visitor's question.** Confirmation levels, sources and map keys are the builder's concerns and sit at the same level as "find a court".
2. **The headline is a scorecard.** "10,257 venues · 4,521 named (1,620 confirmed) · 39 of 81 sports found" tells the owner how the data is doing; a visitor cannot act on it, and "named" and "confirmed" are insider words. It is the first thing read.
3. **Four audiences share one panel** (player, spectator, gatherer, contributor), and the player's controls are mixed with the others'.
4. **Legends are scattered** (ring key under the count, map key under the list, wall legend, popup badges), so the visitor has to learn the colour system before trusting any pin.

## 4. Target design: one question at a time

Principle: **answer the visitor's question first; reveal how we know it second.** Nothing is deleted (every honesty label and link stays, per `ux_polish.md` "no detail lost"); things are *moved down a level*.

### Level 1: always visible (the 10-second experience)
```
+--------------------------------------------+
| (C) CourtConnect CalNeva                   |
| Find where to play racket sports in        |
| California & Nevada.                       |
|                                            |
| [ Places to play ]  [ Events & meetups ]   |  <- two big tabs, plain words
|                                            |
| Sport  [ Pickleball            v ]         |
| [ Search city or venue... ]  [ Near me ]   |
| Filters (3)  v                             |  <- one collapsed row, shows active count
|                                            |
| 42 places in view                          |
| [icon] Rose Park Courts          Confirmed |
|        Santa Barbara · 6 courts            |
| ...                                        |
+--------------------------------------------+
| Map key · How complete is this data? · i   |  <- footer row, one line
+--------------------------------------------+
```
- **Replace the stats headline** with the one-sentence promise. Move the numbers into the "How complete is this data?" dialog and the footer (they become *proof*, not the opener).
- **Mode buttons:** shorter, plainer names. Suggested: "Places to play" / "Events & meetups". (Current "Play, Practice & Partner Up" is 27 characters and wraps on a phone.)
- **Notes under the sport picker** (people to play with, anywhere, wall note) collapse into **one** line with a "Learn more" disclosure, shown only when relevant to the chosen sport.
- **Legends** merge into a single "Map key" button in the footer; the ring key and wall legend live inside it, shown contextually.

### Level 2: one tap (power use)
- **Filters:** Surface, Access (Public / Members), Offers (Clinics, Leagues, etc.). Already collapsed; add the active count to the label ("Filters (2)") and rename "Access and info" to "Who can play" with plain options ("Open to the public", "Members only").
- **Sport About card** and **Find people to play with** stay as disclosures.

### Level 3: inside the popup, in this order
1. Name, one **trust chip** in plain words: "Confirmed", "Best guess: name from park/school", "Unverified". Keep the exact inferred wording one tap down.
2. What you can do: **Plays**, **Website**, **Directions**, **Join & follow** (these are already first; keep).
3. Details, sources and corrections stays collapsed (already correct).
- Group the badges: today up to four badges can stack on one pin; show the single most important one, the rest in the details.

### First-visit welcome (new, small)
A dismissible 3-line card on first load: "Pick a sport, tap a pin, follow the link to play. Pins show how sure we are. We link out; no bookings or payments." Remember the dismissal in `localStorage` (no cookies, no tracking, consistent with ADR 0013; wrapped in try/catch so it still works if blocked).

### Bring the excitement (inside current scope, no new data)
1. **"This week" strip** at the top of Events & meetups: the next 3 events from the 80 already in the export. Shows the project is alive.
2. **Share a place** button in the popup (copies a link that opens centred on that pin). Players recruit players; this is the cheapest growth loop and needs no accounts. (Share-card/OG preview shipped in #321; a deep-link param may already be possible via `?ref=`, check before building.)
3. **"Missing your court? Add it"** as an early, friendly call to action (it already exists as "Suggest a change"; surface it once, in the footer and empty state).
4. **Sport count as a hook:** "39 racket sports with places on the map" as a one-line proud stat in the footer or About, not the headline.

## 5. How to ship it (PM view)

**Timing risk (important).** The friends beta is running: replies due 2026-10-28, findings 10-29 to 11-01 (`docs/feedback_round.md`), and `ux_polish.md` already warns that a redesign mid-beta muddies the feedback. The changes below are *subtractive* (less on screen, plainer words, no restyle), which is lower risk than Option C, but testers should be told the page changed and on what date.

| PR | Change | Size | Check |
|---|---|---|---|
| 1 | Front-door clarity: new headline/promise, stats move to footer/dialog, shorter mode names, single notes line, "Filters (n)", one Map key | Small, `app/index.html` only | Diff every label before/after for 3 sample venues; 375px and 320px; dark mode |
| 2 | Popup: one trust chip up top, other badges into details | Small | Popup text diff: every line still present somewhere |
| 3 | First-visit welcome card + "This week" strip + Share a place | Medium | Works with localStorage blocked; GoatCounter event for each |
| 4 (after beta) | Visual polish Option A (brand colours, sport icons) per `ux_polish.md` | Medium | AA contrast table |

**How to know it worked** (GoatCounter already counts `venue-open`): share of visits that open at least one venue, share that click a link-out, share that change the sport. Baseline before PR 1, compare after. Plus the usability tester in the beta (the one "not into data or apps").

**Parked on purpose:** more facility scans and coverage leads (roadmap 5, 6), anything social phase B. Not needed to make the door clearer.

## 6. Decisions I need from you

1. Ship PR 1 and 2 now (during the beta, tell testers), or wait until findings land on 11-01?
2. Mode names: "Places to play" / "Events & meetups" (suggested), or keep the current ones?
3. First-visit welcome card: yes or no?
4. Headline: replace the stats with the promise sentence (suggested), or keep both with the stats smaller?
