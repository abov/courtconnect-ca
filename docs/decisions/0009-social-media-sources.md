# 0009. Social media sources (link-out only)

Date: 2026-10-12. Status: accepted (2026-10-12).

## Context
Beach tennis, padel and other small racket sports announce open play, events and schedule changes mostly on Instagram and
Facebook (club pages, groups). We want the map to point people at that fresher information without breaking platform terms,
ADR 0005 (no stored third-party data we may not keep) or ADR 0007 (no logins).

## What is and is not allowed
- Meta's official APIs only expose pages the owner manages, or accounts that pass app review (Page Public Content Access).
  We do not have that, so we do not use the APIs.
- Scraping, automated browsing, or reading logged-in pages and private groups breaches Meta's terms and ADR 0007. Not done.
- Facebook groups are usually private. Never read; only a group's public URL may be listed, if a club publishes it itself.

## Decision (cheapest version)
- Store only a public profile or page URL, and the date we last saw it on the club's own site or an official source. Never copy
  post text, images, follower counts or comments.
- Each handle is labeled by how we found it: `official` (linked from the club's own site) or `reported` (the owner or a
  suggest-a-change submission). A handle found only by search is a lead in `venue_leads.csv`, not a link on the map.
- Shown on the map as a plain "Instagram / Facebook" link-out in the venue panel, with the date seen. No embeds, no feeds, no
  "latest post" preview.
- Clubs and players add or correct handles through the existing suggest-a-change form (ADR 0008).

## Build plan
1. Built without a new seed: rows go in `venue_actions.csv` with `action_type` = `social`, `provider` = `instagram` or
   `facebook`, `verified_on` = the date seen and `evidence` saying where the link was found. They reuse the export and the panel.
   `ci/check_seed_evidence.py` requires an instagram.com or facebook.com https URL for these rows.
2. The map lists them in the venue panel under "Ways to join and follow"; social links do not trigger the "Join online" badge.
3. First batch (2026-10-12): 14 rows for 9 accounts, every one linked from the club's own website (BT Cali Club, Padel Up, Pura
   Padel, The Padel Courts, Padel California, Park Padel, Taktika, South End). Clubs whose sites show no account (Bay Padel and
   others) get none; they are leads.

## Freshness
A handle is rechecked in the bi-weekly refresh (`docs/tournament_refresh.md`): does the link still load, and is the club's own
site still linking to it. A dead link is removed, not guessed at.

## Consequences
- The map stays honest and compliant, but shows no live content: a visitor still has to click through to see the latest post.
- Reaching live schedules would need an approved Meta API integration; revisit only if the owner pursues app review.

## Amendment (proposed 2026-10-19, owner request; needs owner review in the PR)
The owner asked for a sweep of the public Instagram posts of the clubs already linked. This relaxes "automated browsing ... not done" for one narrow case, so it is written down here instead of silently done:
- Allowed: reading **public** profile and post pages logged out, in the browser pane, for the accounts we already list (`official` handles), at low volume (about 12 posts per account, every ~2 weeks). Never log in, never click through a login wall, never read stories, private accounts or groups, never use the owner's session.
- Stored: facts only (event name, date, venue, link, and a plain "club's post, single source" note). Never post text, images, follower counts or comments (unchanged).
- Events need a stated date with the right year; prefer the club's own event page; mark single-source post events as such. Courts or accounts found only in a post are leads (`venue_leads.csv`), not pins or links.
- Not allowed (unchanged): Meta APIs without approval, search/hashtag crawling, Facebook groups, bulk scraping beyond the listed accounts.
- Facebook was not tested and is not covered by this amendment.
