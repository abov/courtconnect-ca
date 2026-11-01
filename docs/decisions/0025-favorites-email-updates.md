# 0025. Email updates for favorites and a home area

Date: 2026-10-25. Status: **proposed** (owner decides). Owner request 2026-10-25. Touches ADR 0015 ("no accounts or personal data until an ADR") and ADR 0019 (agents propose, humans merge). Nothing is built under this ADR.

## Context
Visitors can already save venues in the browser (`cc.shortlist`, `localStorage`, max 30, no server). The owner wants people with a **verified email** to subscribe to those favorites and get an update when something changes at them: new events, and new courts opening in their favorite area, town or zip code or nearby. This is the first feature that stores personal data (an email address), so it needs its own decision. ADR 0024 rejected accounts, matching and posting; this is narrower: one email, no profile, no password, no messages between people.

Constraints that do not change: static site on GitHub Pages, public repo (an email must never be committed or put in a seed, CSV, log or session note), bare-minimum budget and the $20/month agent cap (ADR 0019), links out only, honest labels (inferred stays inferred).

## Proposal
1. **What a subscriber gives:** one email, double opt-in (a confirmation link; unconfirmed addresses are never mailed and expire after 7 days), plus what they follow: venue ids from their favorites, and optionally one home place (city or zip) with a radius (default 10 miles) and sports. No name, no password, no account page; every email carries a one-click unsubscribe and a "delete my data" line.
2. **What they get, at most twice a month** (the refresh cadence, never more):
   - *Your favorites:* new or changed events at a favorited venue (`watch_events`, `social_events`), a venue marked closed, a changed access label or new court count, newly confirmed info.
   - *Near you:* venues new in the refresh inside the home place (city, or zip centroid plus radius), "Opening soon" padel/pickleball pins, new tournaments in range.
   - Nothing is sent if nothing changed. Labels are copied from the data ("reported", "inferred", "confirmed"); the email never says more than the map does.
3. **Where the list lives:** NOT in the repo and not in DuckDB. In a hosted email service with a free tier and built-in double opt-in, unsubscribe and sender-address handling (provider and tier to be checked and priced before choosing; the owner's personal email is never the sender or reply-to, only the project contact). Subscribers carry tags (venue ids, place, sports). The static page posts to the provider's hosted form; no backend of our own to run or secure.
4. **How the digest is made (the scheduled tasks):** a new step at the end of the data refresh (Part 5, `courtconnect-data-refresh`) compares the new `venues.json` and event seeds with the previous export and writes a **change feed** (`app/data/changes.json`: venue id, kind, date, label; public data only, no subscriber info). A separate small step turns the feed into one digest per tag set. The feed is public and useful on its own ("what's new" strip, RSS), so the first slice builds no email at all.
5. **Draft mode first (ADR 0019 stage 0):** the agent prepares the digests and the owner approves each send for the first 3 cycles; unattended sending is a later switch like the R0 merge gate, only after a bounce, complaint and unsubscribe check. An agent never reads the subscriber list; the provider merges tags at send time.
6. **Legal and abuse basics, before launch:** a privacy notice (what is stored, who the processor is, how to delete), CAN-SPAM footer with a postal contact (needs a project address; decide which), CCPA/CPRA delete handling, and no one under 13 (the form asks for 13+ in one line; no age data is collected). Not legal advice; the lawyer's read from ADR 0024 applies here too.

## Prerequisites (verify before any build)
- Venue ids must be stable across refreshes (`vid[:10]` in `export_app_data.py`; the shortlist note of 2026-10-22 left this unchecked). If ids drift, a favorite silently stops matching. Add a CI check that ids from the previous export survive, or a rename map.
- Zip to location: need a ZIP/place centroid table (Census ZCTA, public). City boundaries already exist (`raw.census_boundaries`); zip centroids do not.
- A change feed only works if "new" is well defined: first-seen date per venue in the export. Today the export has no such field.

## Options
| | What it is | Cost | Risk |
|---|---|---|---|
| **A. Change feed only** | Public `changes.json` + a "What's new" strip and RSS; no email, no personal data | Small | None new |
| **B. Provider-hosted list (recommended after A)** | Double opt-in form, tags per favorites and place, digests sent through the provider | Free tier to verify; owner approves early sends | Stores emails at a processor; deliverability; unsubscribe and delete duty |
| **C. Own backend** | Serverless function + database + mailer | Hosting + upkeep | We hold and secure the emails; out of budget |

## Decision (proposed)
Build **A first** (no personal data, needed by B anyway), run **B** only if the beta shows people want it (add a question to `docs/feedback_round.md`: "Would you want an email when something changes at a saved spot or near you?") and the owner picks a provider, sender address and privacy text. **Reject C.** Digests stay draft-mode until the owner switches sending on.

## Consequences
- CLAUDE.md "After beta" gets one line for this ADR. README ADR count moves to 0025 (0023, 0024, 0025 proposed).
- If accepted: Part 5 of the scheduled chain gains the change-feed step; no new scheduled task or send happens until B is approved. No existing task is changed now.
- Risk: email is the first thing that can reach a real person, so a wrong closure or stale event goes straight to an inbox. The "nothing sent unless changed", honest-label and owner-approves-first rules are the guard.
