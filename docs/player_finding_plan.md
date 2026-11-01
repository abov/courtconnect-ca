# Plan: find players by age group and level, for every sport

Status: PLAN ONLY (2026-10-29), nothing built. Owner idea 2026-10-29, listed under "After beta" in CLAUDE.md. Builds on social phase A (ADR 0021) and stays inside ADR 0024 option B (discovery over link-outs). Rank with beta findings: question 8 in `docs/feedback_round.md`.

## What is true today
- `social_events.csv`: 21 recurring series, 16 of them Padel. `skill_level` (free text) is filled on 12, `age_focus` on 2, `audience` on 3. Both are only what the organizer states.
- `player_platforms.csv`: 10 apps (Hitch, Courtmate, Playtomic, UTR, ConnectPlayers, ...), mostly Tennis / Padel / Pickleball.
- `player_groups.csv`: 3 WhatsApp communities, all Padel.
- So other sports (Badminton, Table Tennis, Squash, Racquetball, Pickleball outside apps) have almost nothing, and no row says "juniors" or "50+" in a structured way.

## Rules that do not change
No accounts, no data about individual people, no matching, no moderation job (ADR 0024). Links out only. A group is "reported" unless the organizer's own page shows it. Age and level are **inferred unless the group's own page states them**; blank beats a guess. Juniors: show a group's stated age focus, never a way to contact a minor.

## Three parts (each its own small PR; ask in the beta before building any)
**1. Age band and level on what already exists.**
- Add `age_band` (`juniors`, `adults`, `50_plus`, `60_plus`, blank) and `level_band` (`beginner`, `intermediate`, `advanced`, blank) plus `level_scale` (the sport's own words: NTRP, DUPR, UTR, Badminton level, "all levels") to `social_events.csv`, `player_groups.csv` and `player_platforms.csv`. Fill only from the group's own page, with the quote in `evidence`.
- Filter chips in the Watch & Social view; a chip with zero rows is hidden, not shown empty. Export keys `ab` and `lb` (update `export_app_data.py` docstring, `app/data-dictionary.md`, `app/llms.txt`).
- Dbt tests: accepted_values on both bands, evidence required when a band is set.

**2. Where each sport's players actually gather.**
- One short list per sport (all 63 in the sheet is too many: start with the 8 that have the most venues): national-body finder pages, Facebook / WhatsApp / Discord / Reddit groups, Meetup, club ladders, rec-league pages. Public pages only, https only.
- Stored as `player_groups.csv` rows (platform + sport + area + URL + evidence + `verified_on`), refreshed by the scheduled step 2d; stale rows are dropped at the 35-day check like events.
- Success: every one of the top-8 sports has at least 2 ways to find people in each of the 5 biggest metros, or an honest "none found yet".

**3. "Start one" where a city has no group.**
- A starter kit shown only when the chosen sport and area have no group: suggested venue from the map (public, free or low-cost, from `venues.json`), ready-to-post text, and link-outs to start a Meetup, WhatsApp community or Partiful event. The app hosts nothing and stores nothing; the person posts it themselves.
- The suggested venue is labelled by its confirmation level; never suggest a members-only place.

## Order of work
1. Beta question 8 first. If most testers say neither level nor age matters, stop after part 2.
2. Part 2 for the top-8 sports (data only, no UI), then part 1 on the same rows, then the chips, then part 3.
3. Re-check `make usage`: do Watch & Social visits and link-out clicks justify the chips at all?

## Open questions for the owner
- Are juniors in scope on day one, or adults only until a safeguarding line is agreed?
- Which sports first: the top 8 by venue count, or the ones testers ask for?
- Does a Facebook group count as a source when its page needs a login to read? (Proposed: link it, label "reported", never read it logged in, ADR 0007.)
