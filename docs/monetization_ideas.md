# Monetization ideas (brainstorm, 2026-10-29)

Status: ideas only, nothing decided or built. Revisit after the December beta, when usage (GoatCounter, `make usage`) shows which sports and cities get traffic. Rank with RICE in `docs/feedback_findings.md`; an ADR comes before any build.

## Guardrails (from CLAUDE.md and the ADRs)
- Sponsored or paid items never change confirmation levels, ranking or "inferred vs confirmed" labels. Always labelled "Sponsored" / "Affiliate".
- CourtConnect links out; it takes no bookings or payments. Referral link-outs only.
- No partnership or data-license outreach until the owner lifts the 2026-10-16 rule; Pickleheads / Places2Play data stays off limits.
- OSM (ODbL, share-alike) and Overture data cannot simply be resold; only our own layers (seeds, confirmations, events, leads, walls, change feed) carry value.
- Privacy-minimal: no tracking ads; keep GoatCounter-style analytics. Bare-minimum budget, open source (prefer free tools).

## Ideas, by who pays

**Affiliate / referral link-outs** (lowest conflict)
- Gear retailers in the planned "Get started" guide (`docs/sport_recommendation_plan.md`); disclose the link.
- Court-booking apps and lesson / clinic / camp providers: referral fee on the link-out.
- Tournament / league sign-ups and ticketed watch events: referral fee on the registration link.

**Venue and club side**
- "Claim this venue": free basic claim; paid tier for photos, hours, programs, booking link.
- Promoted listings or events (clinics, leagues, tournaments), labelled "Sponsored".
- Lead gen: "new to the sport? ask this club" intro requests sent to clubs.
- Pre-opening promotion for "Opening soon" padel clubs.
- Embeddable "courts near here" widget for clubs, resorts, HOAs, cities; paid white-label branding.

**Sponsorship**
- A brand sponsors one sport view (e.g. padel brand on the Padel filter), or a local pro shop sponsors the "Get started" guide for its city.
- Sponsors for Watch & Social events (organizers, leagues).

**Data and insights (B2B)**
- Coverage and demand reports per metro (courts vs search interest vs usage) for padel / pickleball operators, developers, investors, sport brands, parks departments. Inputs already exist: `make report`, `make usage`, `make interest`.
- Paid API, MCP server (ADR 0023) or change feed (ADR 0025 step 1) for our own layers.
- Consulting for cities / parks departments: court-gap analyses.

**Consumers, community, grants**
- Core stays free. Possible small supporter plan tied to favorites email alerts (ADR 0025).
- Tip jar / sponsors (GitHub Sponsors, Ko-fi, Open Collective); logo merch.
- Grants and sponsorship: parks and recreation / public-health "active living" programs; governing bodies (USTA, USA Pickleball, USA Badminton, US Padel). Mission (ADR 0015) pitches as community benefit.

## Suggested order (if pursued)
1. Affiliate links in the "Get started" guide + tip jar (no rule conflicts; needs the guide first).
2. Claimed / featured venue listings once traffic exists (needs an ADR on labelling and ranking).
3. Insight reports and data / API as the longer-term bet.

## Open questions for the owner
- When to lift the no-partnership-outreach rule (needed for 1 and 2).
- Entity / tax setup before taking any revenue.
- Add a beta question on willingness to pay or to be sponsored? (`docs/feedback_round.md`)
