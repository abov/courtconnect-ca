# Threat model: the agent merge gate (ADR 0019)

Written 2026-10-29 from reading `.github/workflows/agent-merge-gate.yml`, `ci/check_refresh_diff.py`, `.github/workflows/issue-to-pr.yml`, ADR 0019, the repo variables and branch protection (read-only `gh` calls). It is a design review, not a penetration test. Where a gap is listed, the code was checked; nothing was exploited.

## What is at stake
The public map: venue facts, event dates and the links that send people to other sites. There are no accounts and no personal data. A bad change is visible to every visitor but reversible (revert the squash commit, redeploy Pages). The real harm is trust: a wrong link or fact on a site that promises to label what it infers.

## How the gate works
An agent opens a PR from a `claude/refresh-*` branch. When `ci` passes, a workflow runs main's copy of `ci/check_refresh_diff.py` against the PR's files. If every changed file is on a short allowlist and the venue diff is under the caps (2% added or removed, 5% changed, 1% drop), it squash-merges that exact commit and redeploys Pages. Otherwise it comments "escalate" and a person decides.

**State today:** `AGENTS_ENABLED` and `AGENT_AUTOMERGE_R0` are both `true` (the second set 2026-10-25), so R0 auto-merge is on. It has not merged anything: the last five gate runs were skipped, and the last 12 merged PRs were merged by the owner, including the monthly refresh.

## Who is trusted
- **Untrusted:** web pages the agent reads, issue text, forks.
- **Semi-trusted:** the agent and the token and machine it runs on. It can steer or be steered.
- **Trusted:** main's code, the gate script, repo settings.

## What holds (checked in the code)
- The rules come from main, so a PR cannot edit the classifier that judges it.
- The gate never executes anything from the PR. It only reads files, which is what makes checking out PR code with a write token acceptable.
- Forks are excluded, the PR's base must be `main`, and a stale CI run is ignored.
- The merge is pinned to the judged commit (`--match-head-commit`), so a push after classification cannot slip in.
- Two switches (`AGENTS_ENABLED`, `AGENT_AUTOMERGE_R0`) and the required `dbt-build` check.
- Issue text reaches `issue-to-pr` through environment variables, not shell interpolation, and a human `approved` label gates it.
- The app writes data with `textContent` (its only two `innerHTML` uses are static strings), and links must be http or https.

## Gaps
1. **Medium: the "rebuild must equal the export" gate (ADR 0019 gate 7) is not built.** CI builds only the small fixture dataset, and `check_export_fresh.py` checks what the seeds promise. An R0 PR can carry any `venues.json` content that stays inside the caps and the allowlist.
2. **Medium: the caps only look at the `venues` list.** `events` (89), `social` (21), `walls` (448) and `platforms` (10) in the same file are not diffed, so their text and links can change without any limit.
3. **Medium: there is no field-level policy.** A venue counts as "changed" whatever changed, so up to 5% of venues (about 514) can have a website or link swapped to another https site and still classify as R0.
4. **Medium: there is no weekly audit digest and no alert for a missing refresh PR.** ADR 0019 calls both its safety net instead of pre-approval, and no workflow implements them, so detection currently depends on someone reading PRs.
5. **Low: the branch name is coupled to a prefix.** The gate matches `claude/refresh-*`, the refresh agent uses it, but the monthly runbook uses `claude/monthly-YYYY-MM`. That PR is outside the gate, which is safe, but the two will drift unless one name is chosen.
6. **Low: token and machine blast radius is unverified.** The agent runs on the owner's machine. ADR 0019 wants a fine-grained bot token (contents and pull requests only); I did not check which token is in use. A stolen token could push an allowlisted branch.
7. **Low: no concurrency control and admin bypass.** Two refresh PRs could race (the runbook limits it to one), and `enforce_admins` is off, which the owner relies on for `--admin` merges.

## Suggested order
1. Extend `check_refresh_diff.py` to diff every top-level array and escalate any change to a URL-like field (`w`, event `u`/`k`, social `g`/`u`) beyond a small row count. Cheap, local, and it closes 2 and 3.
2. Implement gate 7 in a form that works without the raw data: the agent records a hash of the export and the PR body carries the build log, or the gate rebuilds from a stored raw snapshot.
3. Add the weekly digest and the "no refresh PR in 20 days" alert (ADR 0019).
4. Pick one branch prefix, confirm the bot token's scope, and add a concurrency group to the gate.

## Not checked
The scheduled task's configuration, the agent's prompts and how they resist injected instructions, the token in use, GitHub Pages settings, and anything outside the files and settings named above.
