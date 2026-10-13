# 0010. WhatsApp sources (link-out only)

Date: 2026-10-13. Status: accepted (2026-10-13). Extends ADR 0009.

## Context
Some clubs and organisers run open play, clinics and tournaments through WhatsApp groups or Channels. We want the map to
point people at them without breaking ADR 0007 (no owner logins) or other people's privacy.

## What is and is not allowed
- WhatsApp groups are private and end-to-end encrypted. There is no public search or API for them.
- Reading a group means joining with the owner's own account (ADR 0007) and capturing members' messages without consent. Not done.
- We never search for groups, and never store the name, members or messages of a group we found anywhere other than the
  organiser's own public page.

## Decision (routes 1 and 2)
1. Link-out only: when a club's own public site or public social page shows a group invite link (`chat.whatsapp.com/...`) or a
   public Channel (`whatsapp.com/channel/...`), add it to `venue_actions.csv` as `action_type=social`, `provider=whatsapp`, with
   `verified_on` and `evidence` saying where it was seen. It appears under "Ways to join and follow". Label: official.
2. Organiser-submitted: group admins can send a public link through the suggest-a-change form (new link type "Social or WhatsApp
   link (public)"). It is labeled reported, and only with the admin's consent.
3. Owner-reported events from groups the owner belongs to are typed in by the owner as a note, labeled reported. No message text
   or member names are copied. (Not a code path; a manual practice.)
4. Later, optionally: clubs' public Channels, as link-outs under route 1.

## Build
- `ci/check_seed_evidence.py` accepts `chat.whatsapp.com` and `whatsapp.com/channel` URLs for social rows.
- The map labels the provider "WhatsApp". No new seed or column.
- No WhatsApp rows are added now: none were found on a club's own site yet.

## Freshness
Invite links get revoked. Recheck them in the bi-weekly runbook (`docs/tournament_refresh.md`); a dead link is removed.

## Consequences
Honest and compliant, but shows no live content and misses private groups entirely.
