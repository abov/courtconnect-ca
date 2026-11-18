# ADR 0041: One daily export commits `venues.json`; seed PRs do not

Status: proposed (draft 2026-11-18, needs the owner's OK; nothing below is in force yet)

## Context
- `app/data/venues.json` (5.8 MB, one venue per line) is generated and committed. About 65% of PRs since 2026-11-13 touched it, and it is the file PRs collide on. The merge driver (PR #753) cut PRs needing a merge/rebase/regenerate commit from 42% to about 17% (measured 2026-11-18, PRs after #767), so what is left is the export loop itself: rebuild, re-export, `check_export_fresh`, push again.
- Not generating it at deploy time: CI and Pages only have `ci/fixtures`; the real raw CSVs (1.3 GB) live in the main checkout and, for cloud routines, in the private repo `abov/courtconnect-data`, refreshed by hand. A deploy-time export would need a read token for that repo, and would put the 2026-11-15 failure (stale data repo, 8,300 pins lost) on the live site with no PR gate. `venues.json` is also read by many checks (`check_export_fresh`, `check_venue_drop`, `check_refresh_diff`, `build_changes`, `region_parity`, `check_issues`, `issue_to_pr`, the chatbot tests, `make app`).

## Decision (proposed)
1. **Seed, model and docs PRs do not commit `venues.json`** (nor `changes.json`, `places.json` or `build_stats.json`). They run `dbt build` and stop. No rebuild-rebase-export loop.
2. **One daily export PR** ("Daily export YYYY-MM-DD") from a scheduled routine, run before the 11:17 UTC Pages rebuild: fetch, refresh from `abov/courtconnect-data`, `dbt build`, `ci/check_venue_drop.py`, `make app-data`, `make changes`, PR, merge when `dbt-build` is green. Pages deploys itself because the PR touches `app/**`. A routine that fails `check_venue_drop` commits nothing.
3. **Exceptions (a PR may still export):** a new region, a new sport, a monthly refresh, or any change the owner wants live the same day. The merge driver stays for these.
4. **The freshness check moves:** `ci/check_export_fresh.py` and the pre-push hook run it only when the PR touches `app/data/venues.json`; on other PRs it is skipped. The daily export PR always runs it, and `pages.yml` gains a step for it, so a seed promise that never reaches the export (a watch event, social series, vacation, also-played sport) still fails within a day.
5. **Checks that read `venues.json`** (`region_parity`, `check_issues`, `issue_to_pr`) see data up to 24 hours old. `region_parity --strict` for a new region is run on the export PR from decision 3.

## Consequences
- Saves one rebuild, rebase and push loop per PR (the cost found in `docs/ops_metrics.md`) and nearly all `venues.json` merge conflicts.
- The live map lags a seed merge by up to a day (a pin, a link-out, a closure). A seed PR whose point is "show it today" uses the exception in 3.
- One more scheduled routine to keep healthy; it depends on the data repo being current (unchanged risk, guarded by `check_venue_drop`).
- Honesty is unaffected: nothing is shown that the seeds do not say, it just appears with the next export.

## To implement if accepted
- Routine prompt in `docs/cloud_routines.md` (daily export); `docs/merge_conflicts.md`, `docs/monthly_refresh.md` step 8, `.claude/skills/ship-pr/SKILL.md` and the CLAUDE.md lines about committing `venues.json` change.
- `ci/check_export_fresh.py` and `.githooks/pre-push`: skip when `venues.json` is not in the diff; add the check to `pages.yml`.
- Measure again after two weeks with `make ops-metrics`; revert if the lag costs more than the loop did.
