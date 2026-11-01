# 0024. Social phase B: what "find people to play with" becomes after phase A

Date: 2026-10-23. Status: **proposed** (owner decides). Builds on ADR 0015 (phase B needs its own ADR) and ADR 0021 (phase A, closed 2026-10-21). Nothing is built under this ADR.

## Context
Phase A is live and link-out only: the Watch & Social view (`social_events.csv`, 21 recurring series, 20 from the organizer's own site and 1 WhatsApp, mostly Padel), `player_platforms.csv` (10 apps and groups that match players, all run by others) and `player_groups.csv` (empty header; the scheduled step still looks for public groups, no shelf is planned). ADR 0015 said phase B (own accounts, partner matching, event posting) comes "only if beta findings show people want it, if at all". The beta round has not run yet (`docs/feedback_round.md`), so there is **no demand evidence yet**. This ADR picks a direction so the question is closed on paper, and names what evidence would reopen it.

Constraints that do not change: no owner logins (ADR 0007), no personal data stored (ADR 0015, 0019), links out and no bookings or payments, bare-minimum budget with a $20/month agent cap (ADR 0019), static site on GitHub Pages, one part-time owner.

## Options
| | What it is | Stores people's data? | Needs moderation? | Ongoing cost |
|---|---|---|---|---|
| **A. Stop at phase A** | Keep what exists; refresh series at each sync | No | No | Sync time only |
| **B. Better discovery, still link-out** | A "Find people" filter or shelf over existing data: series by level / age focus / audience, the platforms list per sport, groups per area. Organizers (not players) can submit a public link through the existing suggest-a-change form (ADR 0008, 0010) | No (organizer's public link only) | No (same PR review as every link) | Small; more rows to re-read each sync |
| **C. Posting board, no accounts** | Players post "looking for a partner" through a form; a person or agent approves; posts appear as pins | **Yes**: free-text, a contact route, a place and time a person will be | **Yes**, every post | Daily review; no budget for it |
| **D. Own accounts and matching (connectplayers.ca style)** | Profiles, skill rating, chat or match requests | **Yes**: identity, location, contacts, messages | **Yes**, plus reports, blocks, takedowns | Backend, auth, database, email, abuse tooling, legal terms |

Why not copy connectplayers.ca: it and `player_platforms.csv`'s other nine entries (Hitch, Courtmate, Matched Point, PairUp, Playtomic and others) are phone apps built for exactly this. With no users, no budget and a static site, CourtConnect would start with an empty network against apps that already have one, and a matching network only works with enough people in the same place and sport. What CourtConnect has that they do not is the venue and event data. Linking to them (already done) keeps that advantage without competing.

## Burdens that options C and D would take on
- **Contact details and location.** A partner post or profile ties a named person to a place and a time. That is personal data under California (CCPA/CPRA) and Nevada privacy law, needs a privacy policy, deletion on request and breach handling, and conflicts with "no personal data stored" (ADR 0015, 0019). Not legal advice; a real launch needs a lawyer's read.
- **Minors.** Juniors play every racket sport and some series already say "juniors" or "18+" (ADR 0021). A site with accounts has to decide how to handle under-13 users (COPPA) and 13-17 users, and how adults and minors can contact each other. Doing this safely needs age checks and rules we cannot staff. Link-outs push that burden to the platform that already carries it.
- **Safety and moderation.** Meeting strangers at a court brings harassment, scams, spam, impersonation and worse. A report-and-takedown process needs someone reachable every day. ADR 0019's agents cannot do this: they read untrusted text and are built to propose edits, not to judge people, and a wrong call here harms a person, not a court count.
- **Logins and platform rules.** Reading anything behind a login is off limits (ADR 0007). That also blocks pulling attendee lists or member names from Meetup, Partiful, WhatsApp or booking rosters (ADR 0010, 0012, 0021), so a "who's going" count can only come from our own accounts, which is option D.
- **No bookings or payments.** All four options stay inside this rule. Option D would drift out of it as soon as users ask to split a court fee or reserve a slot; a no would have to be held.
- **Cost.** A and B cost owner minutes at each twice-monthly sync. C costs daily review time. D adds hosting, a database, auth, email, abuse tooling and legal terms, and a person on call. None of C or D fits the bare-minimum budget or ADR 0015's goal of driving owner review toward zero.

## Decision (proposed)
1. **Recommend A now, with B as the only follow-up.** Phase A stays the product. The "Find people to play with" need is met by links to people who already run groups and apps.
2. **Reject D** (own accounts, matching, chat, "I'm going" counts) and **defer C**. Neither is built, and no ADR 0019 agent is given a moderation job.
3. **B is the cheap next step, and only if the beta asks for it** (see triggers). It adds no new data class: filters and a short per-sport "ways to find people" list over `social_events.csv`, `player_platforms.csv` and `player_groups.csv`. Organizers may submit a public link; players cannot post.
4. **Honest labels.** The About text says CourtConnect links to groups and events that others run, does not match people and does not vouch for them. A group link is "reported" unless the organizer's own site shows it (ADR 0010).
5. **Reopen C or D only with all of these:** (a) beta or GoatCounter data showing repeated demand for finding partners in a place where no existing group or app covers the need; (b) a named person who will do moderation; (c) a lawyer's read on privacy and minors; (d) a monthly cost the owner accepts, written into a new ADR. Without all four, this stays closed.

## Consequences
- CLAUDE.md "Open" list: replace the "Social / open-source next step (phase B, own ADR)" line with "Social phase B: ADR 0024 (proposed) recommends stopping at phase A; option B (discovery filters, link-out only) only if the beta asks for it; own accounts/matching rejected." Once the owner accepts, mark the line done.
- Beta question 7 in `docs/feedback_round.md` (added with this ADR): "Did you find someone to play with through the site? Would you want to post that you are looking for a partner?" so the reopen test has data.
- No new seeds, models, app code or data stored. ADR 0015's "until phase B has an ADR, no user accounts or personal data" still holds; this ADR, if accepted, keeps it true.
- Risk of the recommendation: if the beta shows strong demand, stopping at phase A leaves a gap that other apps fill. That is acceptable under the budget and safety limits, and the reopen test above is the way back in.
