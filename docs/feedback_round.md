# Feedback round plan (friends beta)

Goal: learn whether CourtConnect helps people find a place to play and what is missing, before deciding between open source and a paid layer. Output: a ranked backlog and real numbers for `docs/case_study.md`.

## Before you start (owner, one-time)
1. Turn on analytics (ADR 0013): set `GOATCOUNTER_CODE`, merge, re-run `pages.yml`. Record the start date; counts before it do not exist.
2. Note the baseline from `docs/data_quality.md` (venues, named %, events) so you can say what changed during the round.

## Who (6 to 10 people)
Mix on purpose: 2 tennis, 2 pickleball, 1 padel, 1 beach tennis or squash, 1 badminton or table tennis, plus 1 person who is not into data or apps (usability check). Include at least 2 who live outside the Bay Area/LA, to test coverage elsewhere. Ask first; do not add anyone to a list.

## How long
Two weeks: days 1-2 invite, days 3-12 use, days 13-14 wrap-up call or message.

## What each person does
Send this, in your own words:
1. Find a place you could play your sport near you this week. Did you find one you did not already know?
2. Find an open-play session or clinic and follow the link. Was it right?
3. Look for something you know exists (your club or a favourite court). Is it there and correct?
4. Open a place and use "Suggest a change" for something wrong (optional).
5. A week later: did you use the map to actually go anywhere?

## Questions (5 minutes, async is fine)
- Did you find what you wanted? (yes / partly / no) and what was missing?
- Anything wrong or out of date? Which place?
- Did the labels (confirmed, inferred, reported, members) make sense? Did you trust the map more or less because of them?
- What would you use it for weekly? What would make you open it instead of Google Maps?
- Would you pay for anything here (for example club-managed listings, alerts for open play)? How much, honestly?
- Who else would use it?

## What the data will say (GoatCounter, ADR 0013)
| Question | Measure | First targets (adjust after week 1) |
|---|---|---|
| Is it used? | page views, visits per person | most invited people open it 2+ times |
| Does it deliver? | link-out rate = `linkout` / `venue-open` | 25% or more |
| Where do people look? | `sport` events vs coverage | the top 3 requested sports have 20+ venues |
| Do people contribute? | `suggest-change` + `osm-edit` | at least 3 suggestions in two weeks |

State numbers as they are. With 6 to 10 people they are directional, not statistics; say so in the case study.

## Capture
One row per finding in a sheet (or `docs/feedback_log.md`): date, who (initials only), sport, area, type (bug / missing place / wrong data / confusing label / feature idea / pricing), what happened, severity (1-3), source (call / message / analytics). Do not store anything people would not want public; use initials.

## After the round
1. Group findings into themes; fix wrong data immediately through the normal seed workflow (evidence + `make build`).
2. Score the rest with RICE (reach, impact, confidence, effort) in a short table and pick the next three items. Put the table in `docs/feedback_findings.md`.
3. Publish a short changelog ("you said, we did") and thank people.
4. Fill in the placeholders in `docs/case_study.md` (usage, friend feedback) and the scorecard's trend.
5. Decision note (new ADR if it changes direction): stay personal, open source, or test a paid layer.

## Risks
- Low sample: treat as discovery, not proof.
- People are kind: ask what they actually did, not whether they liked it.
- Coverage gaps outside the Bay Area/LA will dominate feedback; record them, then compare with the data-quality scorecard before building anything.
