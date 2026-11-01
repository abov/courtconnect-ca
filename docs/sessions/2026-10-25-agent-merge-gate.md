# 2026-10-25 Merge gate for refresh PRs (ADR 0019, class R0)

Owner asked to start auto-merge. Added `.github/workflows/agent-merge-gate.yml`: after `ci` passes on a `claude/refresh-*` PR it runs main's `ci/check_refresh_diff.py` on the PR's files (the PR cannot change its own rules), comments R0 / R3 on the PR, and merges + dispatches `pages.yml` only if `AGENTS_ENABLED` and `AGENT_AUTOMERGE_R0` are both `true`. Untested until a refresh PR runs it (shadow first). Tournament PRs stay human-merged.
Owner steps to go live: (1) branch protection on main: required approving reviews 0 (keep required check `dbt-build`); (2) repo variable `AGENT_AUTOMERGE_R0=true`. Revert path: set the variable to false, or `AGENTS_ENABLED=false` stops all agents.
