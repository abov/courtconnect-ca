# 0007. Confirmation levels and a leads backlog

Date: 2026-10-10. Status: accepted.

## Context
Hand-added venues (a ping pong table at a park, badminton open play at a rec centre) vary in how well we know them.
The map must not present a rumour and a site visit as the same thing.

## Decision
- Every `manual_venues` row has `confirmation`: `visited` (seen in person, with `confirmed_on`), `official` (stated on the
  operator's or a government page), or `reported` (a third party said so). The map shows the level as a badge.
- Claims that cannot yet be placed or checked go in `venue_leads.csv` (status new, needs_location, needs_visit, confirmed, resolved,
  rejected). Leads are never shown on the map; `mart_venue_leads` is the to-do list.
- Public reports come in through the "Report a venue" issue form, with no personal information.

## Sources for finding leads
Yelp, Reddit and similar are leads only: read them by hand, record the link in `source_url`, never scrape or store their content.
Better sources: city recreation program pages, club and league sites, USATT-style directories (check terms first), and adding tables
to OpenStreetMap directly (`sport=table_tennis`), which flows into this project for free.

## Accounts and logins
We do not use the owner's (or anyone's) logins to Playtomic, PlayByPoint, Padel Up or similar. Automated use of a logged-in session
likely breaches their terms, risks the account, and exposes other members' data. Anything the owner sees while logged in can be
reported by them and recorded as owner-reported with a date. Public pages, clubs' own sites, and partner programs are the routes.
