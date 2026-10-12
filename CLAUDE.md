# CourtConnect California

Racket-sport venue finder for California: Python ingestion -> dbt (DuckDB dev/CI, Snowflake prod) -> static MapLibre map in `app/`.
README.md has the full story; read it only if you need background. Decisions are in `docs/decisions/` (ADRs 0001-0006).

## Commands (run from Git Bash on Windows)
- `make build`      dbt seeds + models + tests (the main check; run after any change to `transform/`)
- `make app-data`   export `app/data/venues.json` for the map; `make app` serves it at localhost:8765
- `make extract` / `make load`   refresh raw data (extract takes ~15 min; don't run unless asked)
- `make check-links` / `make check-websites`   verify link-outs / flag dead venue sites
- `make report`     regenerate `docs/coverage_snapshot.md`
- `make snowflake-build`   same project on Snowflake (needs credentials in `.env`)

## Rules
- NEVER read, print or commit `.env` (credentials). `.env.example` shows the keys.
- Never hand-edit `transform/seeds/all_racquet.csv` or Snowflake `RAW.ALL_RACQUET`: the Google Sheet is the source, `make sync-sports` overwrites them.
- Data edits go in seeds, then `make build`:
  - `manual_venues.csv` (venues no dataset knows), `venue_actions.csv` (link-outs; keep `verified_on` + `evidence`),
  - `watch_events.csv` (https links only), `place_sport_overrides.csv` (confirm/reject uncertain matches), `sport_aliases.csv`.
- Models must run unchanged on DuckDB and Snowflake: use `adapter.dispatch` macros, no engine-specific SQL.
- Honesty over polish: label inferred data as inferred, never present guesses as confirmed. CourtConnect links out; it takes no bookings or payments.
- NEVER use the owner's logins (Playtomic, PlayByPoint, Padel Up, etc.) or read logged-in pages; use public pages and what the owner reports (ADR 0007).
- Don't use Google Places data (terms forbid storing it); Overture + OSM only (ADR 0005).
- Ignore generated/bulky paths when searching: `transform/target`, `transform/logs`, `courtconnect.duckdb`, `app/data/venues.json`.

## Keeping usage low
- Don't take browser screenshots unless I ask. Read pages as text (`get_page_text` / `read_page`) instead.
- In auto mode (or whenever I haven't picked an approach), always choose the cheapest path that does the job, and say in one line what it is:
  - Do it directly with Grep/Read/Edit; don't spawn subagents, run deep-research, or use extended web search unless I ask.
  - Run the narrowest check (`dbt build --select <changed models>`, one test) before the full build; run the full build once at the end.
  - Never start `make extract`/`make load`/`snowflake-build`, or loops/scheduled tasks, without asking.
  - Prefer one batched tool call over many; stop once the task is done instead of extra "nice to have" work.
  - If a task looks expensive (many pages to research, big refactor), propose the cheaper scoped version first and wait for my OK.
- Read only the lines you need from big files; don't dump whole CSVs, logs or `venues.json`.
- One task per session. Keep sessions small: when context passes ~200-300k tokens, update "Current status" below and tell me to start a fresh session.
- At the end of a session, update "Current status" (2-3 lines) so the next session can pick up without a long history.
- Use a lighter model for simple edits; save the biggest for hard problems.

## Where things are
- `ingestion/`   Python extract/load/export scripts
- `transform/`   dbt project (models, seeds, macros, tests)
- `app/`         static map page
- `ci/fixtures`  small sample data for CI

## Current status
Phase 1 done (link-outs, confirmation levels, leads, contributor workflow, extra sports). `main` is branch-protected (PR + `dbt-build`; owner can bypass). Build: `.venv/Scripts/dbt build --project-dir transform --profiles-dir transform` (no `make` in Git Bash; run it where `courtconnect.duckdb` is, a worktree needs a copy).
Session 2026-10-10 (uncommitted on branch `claude/jolly-turing-7d6584`): (1) access toggle done: `dim_venue.is_members_only` (access private/members, not marked public) -> mart -> export bit 8 -> app "Public / Private-members / Both" (default Both; ~1,457 venues are private/members, mostly OSM `access=private`, incl. residential courts). (2) Seeded South End and Equinox LA/Irvine (official), West End (reported); Manhattan Country Club added with an INFERRED location (18 unmapped OSM tennis courts at Parkview Ave/Village Dr); lead for other Equinox clubs. (3) `docs/sport_directories.md`: only Outdoor Racquetball has a directory (lead `outdoor-racquetball-wor-list`); other 9 sports searched, none found. Coverage snapshot refreshed.
Session 2026-10-10b (PR #3): private-club pass 1 read ~90 clubs' own sites (bulk-fetched, public pages only). Added 29 members/private clubs (official; many 'members only' INFERRED, see evidence) and 8 public clubs to `manual_venues.csv` (Bay 12, LA 6, OC 5, SD 6), plus 45 `venue_leads.csv` rows (`*-access`) for clubs whose page did not say. List is INCOMPLETE; ~500 more club-named venues untouched (golf/country clubs mostly: Riviera, LACC, Bel-Air, Burlingame, Menlo etc. need their own pages). Build passes (only the known warning).
Session 2026-10-11: Taktika Carson + Point Loma (inside Barnes Tennis Center) added; no public open-play times exist, Carson open play is owner-reported. Added the map "Suggest a change" link -> `suggest-a-change` issue form -> `approved` label -> `issue-to-pr.yml` PR (ADR 0008 update), plus `ci/check_seed_evidence.py`. Untested live: the workflow's `gh workflow run ci.yml`. `assert_all_racket_sports_loaded` warns because the sheet has 75 sports and the test expects 76 (owner: add the missing sport or lower `expected_racket_sports`). Create the `approved` and `venue-change` labels. Two old rows (btcc-manhattan-beach/hermosa-beach) have no `confirmed_on`.
Tournament passes 1-3 done (43 events; bi-weekly refresh runbook in docs/tournament_refresh.md, scheduled task `courtconnect-tournament-refresh`; gaps in docs/tournament_sources.md). Next: work the `*-access` leads (need a call or deeper page read) and the remaining club-named venues; check the other-Equinox lead; directories pass 2 is done (docs/sport_directories.md): USA Racquetball list is link-out only, ~40 sports searched with no usable directory, 10 small ones not searched yet. Other open items: reviewers as collaborators (owner's call); optional OSM padel fixes by the owner. Pages is manual-only: it was redeployed 2026-10-11 so the live site has the "Who can play" filter; re-run `pages.yml` after any app change. Unchecked: the `assert_all_racket_sports_loaded` warning.
Session 2026-10-11b (uncommitted, branch main): hid Indoor/Outdoor/Lights chips in `app/index.html` (code kept; URL `on=` ignores them). `sport_also_played.csv` now maps Pickleball -> Typti/Skyball/Spec Tennis/Lite Tennis and Badminton -> Pitton (new column `exclude_private_members`; court-level via OSM access, place-level via club-style names). Build passes (known warning only). skyball.us/play shows "No tournaments currently scheduled" to a plain fetch (past list is probably JS-loaded). Tournament sweep NOT done yet: needs a scoped plan from the owner. Re-run `pages.yml` after merging.
