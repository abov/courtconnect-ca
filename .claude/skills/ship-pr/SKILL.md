---
name: ship-pr
description: Take finished RacketConnect work from a branch to a merged, deployed change. Use when the user says "open a PR", "ship it", "merge", or the work is done and needs a PR. Covers pre-flight checks, full build, venues.json export, PR, the one "Ship it?" confirmation, admin squash merge, Pages deploy and live-site check.
---

# Ship a PR (RacketConnect)

Rules that always apply: merge only after `dbt-build` is green AND the owner says "ship it" in chat (an agent-opened PR still needs that yes). Never bypass failing checks. Keep every summary short (PR body 2-4 bullets, commit one line plus at most two).

## 1. Pre-flight (before opening)
1. `git fetch`; `git log origin/main --since=1.day --oneline`; `gh pr list`. If another PR or commit already did this work, stop and say so.
2. Sync with main (rebase or merge). If `app/data/venues.json` conflicts, never hand-resolve: take main's copy, run `dbt build --full-refresh`, `make app-data`, commit.
3. Pick the narrowest check that proves the change, then ONE full build before the PR:
   `.venv/Scripts/dbt build --project-dir transform --profiles-dir transform` (add `--full-refresh` if a seed gained a column). A new worktree with no `courtconnect.duckdb` needs `python ingestion/fresh_db.py` first.
4. Seed/model change: `make app-data` (no make in Git Bash: `python ingestion/export_app_data.py`) and commit `app/data/venues.json`. Check `python ci/check_export_fresh.py`.
5. Doc added/renamed/removed or a live page/tool link changed: update `docs/README.md` (`python ci/check_docs_hub.py`). Tool/library/service/source added or removed: update the Tool Dictionary row and `docs/tools_and_strategies.md`.
6. Sport names touched: `python ci/check_sport_names.py`. New region: `python ci/region_parity.py --region XX --strict`.
7. Never commit `.env`, `courtconnect.duckdb`, `transform/target`, `transform/logs`.

## 2. Open the PR
- One-line commit(s); PR body 2-4 bullets: what changed, what is not verified, what is next. Hand-off lives in the PR; do not add a session note or edit a shared log.
- After `gh pr create`: call `mcp__ccd_pr__get_status`; if it does not report the PR, `mcp__ccd_pr__bind_pr`. Read CI there and offer Auto-fix. Do NOT poll CI yourself (no cron, loop, ScheduleWakeup, Monitor or `gh` polling).

## 3. Ask once
When `dbt-build` is green, ask a single question, "Ship it?", with one button. No "Not now" filler.

## 4. Merge (only after the explicit yes)
1. Sync with main again right before merging (rebase/merge; re-export venues.json if it conflicts).
2. `gh pr merge <n> --squash --admin`, only when the sole blocker is the review rule (no reviewers yet).
3. Confirm the PR state is MERGED (`gh pr view <n> --json state`). Do not call it shipped before that.
4. If the merge touched `app/**` or `pages.yml`: `gh run list --workflow pages.yml --limit 3`; a newer run cancels an older one, so check the latest. Run `gh workflow run pages.yml` only if no run started.
5. Check the live site as text (no screenshots): <https://abov.github.io/courtconnect-ca/>, with `get_page_text`/WebFetch for the changed thing.
6. Report in 1-2 lines: merged, deploy status, what you checked live.
