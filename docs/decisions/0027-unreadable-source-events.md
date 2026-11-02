# 0027. Events whose source cannot be read leave the map instead of waiting for a person

Date: 2026-11-02. Status: **proposed** (owner decides). Follows the 2026-11-01 refresh (PR #463), where the "oldest upcoming-event check" SLA failed because four seeded events had sources no scheduled run could read (`padelusa.org/calendar` loads by script, a club page returned 404, an Instagram post needs a login) and a person was needed to re-read them.

## Context
- `watch_events.csv` rows carry `verified_on`; the scorecard SLA fails when any upcoming row is older than 14 days. Re-dating a row without reading its source would fake freshness (CLAUDE.md: honesty over polish; ADR 0019: no loosening a gate to get green).
- Scheduled cloud runs read public pages only (ADR 0007, 0009). Some sources can never be read that way: login-walled social posts, script-only calendars, pages that disappear.
- Today an unreadable source leaves the row stale, the gate red, and the PR waiting for a human.

## Decision (proposed)
1. **Prefer a readable source.** When a seeded event's source cannot be read, first look for a readable one: the organizer's own page, the governing body's list (cloud: `ingestion/read_usa_padel_list.js` for USA Padel, headless Chromium), a registration page. A readable source that confirms the event re-dates the row.
2. **Two misses move it to leads.** If the source could not be read (or no longer shows the event) on two consecutive scheduled runs, the run moves the row from `watch_events.csv` to `venue_leads.csv` (`status new`, `claim` = what the source said, `notes` = why and the date), never deletes the evidence, and lists it in the PR under "needs owner decision". One miss only adds a note to the PR; no change.
3. **Different dates win.** If a readable source shows other dates, the run corrects the row and says so in `source_note`.
4. **A lead is added back** as a watch event only when a readable source shows the event with dates (every run rechecks leads of this kind).
5. **No new status, no gate change.** Rows stay `confirmed` / `dates_not_confirmed` as today; the SLA keeps its 14 days. The run never edits `verified_on` without a read.
6. **Out of scope:** closing venues, link-outs or social series (those stay evidence/judgment steps under ADR 0017 and 0019).

## Consequences
- The refresh no longer stops on events nobody can verify; the map shows less rather than something it cannot back up. A real event can be briefly missing until a readable source appears or someone reports it (suggest-a-change form).
- Implementation if accepted: a step in `docs/refresh_agent.md` (step 5c: re-read upcoming rows older than 10 days) and Part 3/4 of `docs/tournament_run_parts.md`, a miss counter kept in the lead's `notes`, and a CI check that every moved row has a lead.
- Risk: a source that fails twice because of a temporary outage moves a good event. Mitigation: leads are visible in the PR, one-line revert, and the next run re-adds it when the source reads again.
