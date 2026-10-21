# 0021. Social get-togethers as recurring series (Social mode), no turnout or age prediction

Date: 2026-10-21. Status: accepted (2026-10-21). Builds social phase A of ADR 0015; same link-out rules as ADR 0009, 0010 and 0012.

## Context
The owner asked for social events (Padel Up, P1 Padel and similar clubs, whose mixers and club nights are announced on their own sites, Instagram,
WhatsApp, Partiful and email), a way to show how big a crowd to expect, and whether age groups could be predicted.
Read 2026-10-21: Padel Up lists "Link Up" (Fridays, Century City, 21+, $15) on its events and booking pages; Culver City lists open play programs, not Link Up.
P1 Padel's weekly programs page lists a men's night, a ladies match-play clinic, a mixed club night, Courts & Coffee and two Saturday mixers.

## Decision
- **Series, not dates.** `social_events.csv` holds one row per recurring series (schedule in the organizer's words, `last_listed_date` = last session their page shows).
  Rows do not go stale each week, and the app hides a series once its listed run has ended. `verified_on` + `source_note` are required (CI `check_seed_evidence.py`).
- **Social lives inside the Watch button (owner, 2026-10-21).** The two top buttons are now "Practice & Play" (venues and hitting walls) and "Watch & Social"; inside the
  second, a switch picks "To watch" (dated events) or "To join" (recurring series). In "To join" there is one pin per venue, a list of series, and a popup that groups the
  venue's series. Every series links to the organizer; CourtConnect signs nobody up and takes no payments. The two views stay separate because one is dated and the other recurring.
- **How a series was found** is stored (`source_kind`: official site, Instagram, Partiful, Meetup, WhatsApp, email, owner report) and shown in the popup.
  Instagram, Partiful and Meetup are read one public page at a time (ADR 0009, 0012); WhatsApp is a link-out only (ADR 0010); email and owner reports are labelled as reports.
- **Age focus and audience are only what the organizer states** (`age_focus`: all ages / juniors / 18+ / 21+ / 50+; `audience`: women / men / mixed). Blank means not stated, never a guess.
- **No turnout prediction and no age prediction.** There is no attendance history to learn from, so a number would be invented. Inferring the age of people from photos
  or follower lists is rejected on privacy grounds. What is shown instead: the schedule, the level, the venue's court count (a fact) as a rough size guide, and any
  organizer-published fee or limit.
- **Rosters stay unread.** Booking systems show "View roster" pages; they list people and are not read or stored (ADR 0007).

## Consequences
New seed `social_events.csv` -> `stg_social_events` -> `mart_social_events` -> `social` array in `venues.json` -> Social mode in `app/index.html`.
Re-read each series page at every twice-monthly sync (`docs/monthly_refresh.md`) and when `verified_on` is older than 35 days.
A later "Find people to play with" shelf for existing Meetup/Partiful/WhatsApp link-outs can reuse this mode. Own accounts, "I'm going" counts and any real turnout
estimate are phase B and need their own ADR.
