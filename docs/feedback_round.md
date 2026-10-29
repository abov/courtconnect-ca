# Feedback round plan (friends beta, December 2026)

Goal: learn whether CourtConnect helps people find a place to play, watch or find people to play with, and what is missing, before choosing between staying personal, open source or a paid layer. Output: a ranked backlog (`docs/feedback_findings.md`) and real numbers for `docs/case_study.md`. Dates are TBD (owner picks the start; the round is 2 weeks).

## Owner checklist before sending
- [ ] GoatCounter (ADR 0013, site `courts`, https://courts.goatcounter.com): exclude your own visits: open the live site once on each device and browser you use (laptop, phone) with `#toggle-goatcounter` added to the address, e.g. `https://abov.github.io/courtconnect-ca/#toggle-goatcounter`; GoatCounter then says tracking is disabled in that browser (it sets a local flag, so it survives changing IP; visit the same link again to turn counting back on); optionally also add your home IP under Settings > Ignore IPs (it changes, and a phone on mobile data uses another one). Date done: ____ (laptop), ____ (phone). Do not quote usage numbers from before it.
- [ ] Write the start date and the baseline from `docs/data_quality.md` (venues, named %, events) at the top of `feedback_findings.md`.
- [ ] Open the live map on your phone once and check the invite steps still match the screens (buttons "Places to play" / "Events & meetups" / "Find players", "Suggest a change" in the popup).
- [ ] Hard-refresh after the last deploy (Pages caches up to 10 minutes).

## Who (6 to 10 people, ask first, no mailing list)
Mix on purpose: 2 tennis, 2 pickleball, 1 padel, 1 beach tennis or squash, 1 badminton or table tennis, 1 person not into apps (usability check). At least 2 live outside the Bay Area and LA (Sacramento, Central Valley, San Diego, Nevada) to test coverage elsewhere.

## Timeline
Day 1 invite (individually, not a group chat) -> day 7 to 10 one check-in -> day 14 replies due -> within 3 days write the findings.

## Invite message
Swap in their sport (step 1) and a place they know (step 2). Give each person their own link tag so analytics can tell groups apart without names: `https://abov.github.io/courtconnect-ca/?ref=friend-padel` (the tag is the sport or area, any `friend-<a-z0-9-up to 20>`; never initials).

> Hey [name]! I built a free map of racket-sport spots in California and Nevada (tennis, pickleball, padel, squash and more) and I'd love your honest take before I decide what to do with it.
>
> Link: https://abov.github.io/courtconnect-ca/?ref=friend-[tag]
>
> About 10 minutes over the next two weeks, phone is fine:
> 1. Find a place near you to play [their sport] this week. Is there one you didn't know?
> 2. Look up [a club or court you know]. Is it there and correct?
> 3. Open a place and tap a link (website, open play, a club's Instagram). Did it go where you expected?
> 4. Tap "Events & meetups" (or "Find players") and look for an event or group. Anything useful?
> 5. Optional: if something is wrong, tap "Suggest a change" on that place.
>
> A text back is fine: did you find what you wanted, what was missing or wrong, would you use it again and for what, anything confusing (like "confirmed" vs "inferred")?
>
> It's early and some areas are thin, so gaps and mistakes are exactly what I want to hear. It only counts anonymous visits (no accounts, no cookies, no names), and I won't share what you tell me with your name on it. Could you get back to me by [date]? Thank you!

Check-in (day 7 to 10):

> Quick check-in: have you tried the map? Even one thing missing or wrong helps. Did you use it to decide where to play this week?

When they reply, ask what they did, not whether they liked it ("What did you search for first?"). If they would pay for something, ask what and how much, once, at the end.

## Questions to cover (any order, async is fine)
1. Did you find what you wanted (yes / partly / no)? What was missing?
2. Anything wrong or out of date? Which place?
3. Did the labels (confirmed, inferred, reported, members only) make sense? More or less trust because of them?
4. What would make you open this instead of Google Maps, weekly?
5. Would you pay for anything (club-managed listings, open-play alerts)? How much, honestly?
6. Who else would use it?
7. Did you find someone to play with through the site (a group, open play, an app we link)? Would you want to post that you are looking for a partner? (Evidence for ADR 0024; "no" is a useful answer.)

## Numbers (GoatCounter, directional only with 6 to 10 people; say so in the case study)
| Question | Measure | First target |
|---|---|---|
| Is it used? | visits per `ref=friend-*` tag | most invitees open it 2+ times |
| Does it deliver? | `linkout` / `venue-open` | 25% or more |
| Where do people look? | `sport` events vs venues per sport | top 3 requested sports have 20+ venues |
| Do people contribute? | `suggest-change` + `report-form` + `osm-edit` | at least 3 in two weeks |
| Do the extras land? | `this-week-open`, `shortlist-add`, `share` | note counts, no target yet |

## How to record (in `docs/feedback_findings.md`)
1. **Log** one row per finding: date, who (sport + area, no names or initials), type (bug / missing place / wrong data / confusing label / feature idea / pricing), what happened, severity 1-3, source (call / message / analytics). Nothing people would not want public.
2. **Fix wrong or missing data now** through the normal seed workflow (evidence + `make build`); mark the row "fixed" with the PR.
3. **Score the rest with RICE** in one table: Reach (people of N who hit it), Impact (3 big, 2 medium, 1 small, 0.5 minimal), Confidence (100 / 80 / 50 %), Effort (person-days), score = R x I x C / E. Take the top three into "Open, in order" in `CLAUDE.md`.
4. **Close the loop:** short "you said, we did" message to the testers; fill the placeholders in `docs/case_study.md` and the scorecard trend.
5. **Decision note** (new ADR if direction changes): stay personal, open source, or test a paid layer.

## Risks
- Low sample: discovery, not proof. People are kind: ask what they did.
- Gaps outside the Bay Area and LA will dominate feedback; record them, then compare with `docs/data_quality.md` before building anything.
- Do not change the look or labels mid-round (visual polish PRs wait until findings are in, or ship before the invite).
