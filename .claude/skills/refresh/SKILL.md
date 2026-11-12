---
name: refresh
description: Run the twice-monthly RacketConnect data refresh (sports sheet sync, issues, extract/load, link checks, build, scorecard, export, change feed, ship). Use when the user says "monthly refresh", "project sync", "run the refresh", or asks to refresh data freshness. Orchestrates the steps in docs/monthly_refresh.md.
---

# Twice-monthly refresh

`docs/monthly_refresh.md` is the source of truth for every step and flag. Read it by step number when you reach that step; do not restate it from memory. This skill only fixes the order, the stop points and the cost rules.

Cost rules (CLAUDE.md): no subagents, no screenshots, public pages only, narrow check before the full build. One task per session; if context passes ~200-300k, tell the user to start fresh.

## Order and stop points
0. Start: `git fetch`, `git log origin/main --since=1.day --oneline`, `gh pr list` (another refresh PR may exist). Branch `claude/monthly-YYYY-MM` from fresh main. Note the last line of `docs/data_quality_trend.csv`.
1. Step 2, sports sheet: `make sync-sports`, then `python ci/check_sport_names.py`; if the sheet changed also `make sport-map`, `make search-terms`, and carry names through seeds, scripts and the app. Never hand-edit `all_racquet.csv`.
2. Step 2b, issues: `make issues`, then `make feedback` (commit `docs/feedback_log.csv`). Form reports: ask the user to mark `review` in the sheet; then `make sync-reports` (needs `REPORTS_CSV_URL`; `ARGS=--dry-run` first).
3. **STOP and ask** before step 3/4 (extract ~15 min, then load). Order inside: `overture_release_diff.py` BEFORE the Overture extract overwrites the raw file; `osm_snapshot_diff.py` AFTER the OSM extract; `reverse_geocode_blanks.py` and `extract_osm_parents.py` after each OSM refresh. `make load`: a shrink refusal (>10%) is a stop-and-look, never `--force` on your own.
4. Step 5: `make check-links`, `make check-websites`, `make check-pages`; re-date `verified_on` only for rows you re-read. Step 5c: `make rank-rechecks ARGS="--top 25"`, reread down to the cap and stop. Social series (5b) is done by the scheduled run unless Part 4 was skipped.
5. Step 6: build (narrow, then one full; `--full-refresh` for new seed columns). After raw data loads, `ingestion/build_changed.py` cannot see the change: use `--full`. Then `make eval-match`.
6. Step 7: `make quality`, `make stats`, `make report`, `make market-snapshot`, then `python ci/check_scorecard_regression.py` (add `--base-ref origin/main`). A failure is explained in the PR or fixed, never ignored.
7. Step 8: `make app-data`; 8a `make changes` and read the printed id drift (over 2% means stop and look); 8b edit `app/data/featured_sport.json`.
8. Step 9: ship with the `ship-pr` skill, PR titled `Monthly refresh YYYY-MM`; add the 2 status lines to CLAUDE.md "Current status" and the row to the Log in `docs/monthly_refresh.md`.

`make` is not in Git Bash: run the command the target wraps (see the Makefile).

## Report (short)
Venues, % seen in 35 days, SLAs met vs last month, anything skipped or breached. Max ~5 bullets.
