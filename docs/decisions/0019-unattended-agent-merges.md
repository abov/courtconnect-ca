# 0019. When agents may merge without a person reviewing

Date: 2026-10-18. Status: **accepted** (owner, 2026-10-18), with the Numbers table as written. **Stage 0 only: agents may open PRs, humans still merge.** **Update 2026-10-25 (owner asked to start auto-merge):** the merge gate for class R0 is built as `.github/workflows/agent-merge-gate.yml` and starts in shadow (it comments its verdict on every `claude/refresh-*` PR). It merges only when the owner sets the repo variable `AGENT_AUTOMERGE_R0=true` and `AGENTS_ENABLED` is `true`; the owner may switch it on before the N-PR track record in the Numbers table, accepting that risk. R1/R2 (including tournament PRs, which are R2 until a code-checked quote exists) stay human-merged. No class may auto-merge until it earns it under section 4 and the owner switches it on; no scheduled task starts without the owner's go-ahead (CLAUDE.md).

## Context
ADR 0015 sets a long-term goal: the project runs itself with the owner's review time driven toward zero. `docs/self_service_plan.md` classifies each refresh step: most are mechanical with a pass/fail result, some need a page read and a quote, a few need judgment. ADR 0008 says a reviewer checks the evidence and merges; ADR 0017 says nothing from the page reader is used without a person approving it. Both were right for a project with no automated gates and no measured accuracy. This ADR says how that changes, and what does not.

The risk is specific. Agents read untrusted text (issue bodies, web pages) and propose edits to data that the public reads. A wrong court count is a small harm; a hostile page that steers an agent, a runaway bill, or a bad bulk edit is a bigger one. So the design is: the model proposes, deterministic code decides, and every merge can be undone.

## Decision

### 1. A model never merges; a gate script does
An agent opens a PR. A separate deterministic **merge gate** (a script run in CI, no LLM) decides whether the PR may merge itself, using GitHub's native auto-merge on required checks. No `--admin` bypass for agent PRs. The gate reads the PR's class (below), its diff and the check results; the model cannot change the rules it is judged by.

### 2. Risk classes
| Class | Examples | Auto-merge when earned |
|---|---|---|
| **R0** routine refresh | monthly extract + load + rebuild + export, scorecard line, status log | yes, after stage 1 |
| **R1** mechanical fixes | link-out `verified_on` re-dated after a successful re-read, dead link removed, city fill, sport-name sync from the sheet | yes, after stage 1 |
| **R2** evidence-backed facts | new/changed seed row (courts, sports, access, address, opening status) with a URL and an exact quote that code verified on the fetched page | yes, per field type, after its own track record |
| **R3** escalate | see the list below | never; PR waits for the owner |

**Always R3 (the escalation list):** closing or deleting a venue on a single source; any change to `closed_places.csv` where the page does not state the closure; raising a confirmation level (ADR 0008 needs two independent sources); home-like pins and anything with personal data (ADR 0016, address privacy); a new data source or any change to what is fetched; changes to ADRs, `CLAUDE.md`, workflows, `ingestion/`, macros, models, tests, the app, `.env.example` or the merge gate itself; adding a sport; any gate failure; any step that needed `--force`.

### 3. Gates every auto-merge must pass
1. All required CI checks green (dbt build + tests, `ci/check_export_fresh.py`, `ci/check_regions.py`, the new ones below).
2. **Path allowlist per class:** the diff touches only the files that class may touch (R0: raw-derived seeds' generated outputs, `app/data/venues.json`, the trend CSV; R1/R2: named seed files). Anything else makes it R3.
3. **Diff cap per class** (owner): for example R2 at most 20 rows and R0 at most 2% of venues changed.
4. **Scorecard no-regression:** venue count does not fall more than 1% (owner), no SLA that passed now fails, "seen in 35 days" does not drop, no new test failures.
5. **Evidence rule:** every changed seed row has `evidence` (URL), `verified_on` set to the run date, and for R2 an exact quote that code found verbatim in the page it fetched itself (ADR 0017 guard rail), not text the model typed.
6. **Independent check (R2):** a second model call, given only the page text and the proposed fields, must reproduce the same facts. Disagreement makes it R3.
7. **Rebuild proves it:** the gate rebuilds from the PR head on a clean database; the PR's `venues.json` must equal the rebuilt export.
8. **Kill switch off:** the repo variable `AGENTS_ENABLED` is `true` and the weekly spend and PR-count caps are not exceeded.

### 4. Stages: classes earn auto-merge by track record
- **Stage 0, draft (now):** agent opens the PR, a person merges. Log each PR's outcome in `docs/agent_log.csv` (class, accepted unchanged / edited / rejected).
- **Stage 1, shadow:** the gate runs and comments "would auto-merge" while a person still merges. Compare its verdict with the person's.
- **Stage 2, auto-merge:** a class switches on after N consecutive PRs accepted unchanged **and** zero gate false-negatives in shadow (owner; suggested N = 20 for R0, 30 for R1, 50 per field type for R2, with measured field precision at or above 95% for R2).
- **Demotion:** one revert, one wrong fact found by the audit, or one gate bypass drops the class back to stage 0 until the owner re-enables it.

### 5. Safety net instead of pre-approval
- **Audit trail:** one bot identity with a fine-grained token (contents + pull requests only, no admin, no workflow edits); every change is a PR with class, evidence and gate results in the body.
- **Revert:** a one-line command and a documented drill (`docs/self_service_plan.md` to be extended): revert the merge commit, rebuild; the revert merge redeploys through `pages.yml` (it runs on pushes that touch `app/**`).
- **Weekly audit digest:** a random sample (at least 10%, minimum 5) of that week's auto-merged PRs is re-checked by an independent AI pass and by the page itself; the owner gets a short digest of disagreements. This is how review time stays near zero and still catches drift.
- **Budget and kill switch:** hard weekly spend cap and PR cap (owner); a failed gate, a revert, or `AGENTS_ENABLED=false` stops all agents.
- **Unchanged rules:** no owner logins (ADR 0007), no Google Places data (ADR 0005), project User-Agent only, no personal data stored, no `.env` read, links out and no bookings or payments. Secrets reach agents only as runner secrets, never in prompts or PRs.

### 6. Untrusted input
Issue text and fetched pages are data, never instructions. The model that reads a page has no tools and returns fixed fields (ADR 0017). Issue-based changes keep today's human `approved` label until the issue's cited page passes the quote check (gate 5) and its class has earned auto-merge; issues from anyone are treated as hostile by default.

### 7. Honest labelling to users
Where no person reviewed a fact, the map says so. The About text may say "checked automatically; a person audits a sample" but never "a person reviews every change". Inferred data stays labelled inferred (ADR 0007). Reported facts do not become confirmed because an agent merged them.

## Numbers (starting values; strict first, loosen with data)
| Setting | Value | Status |
|---|---|---|
| Spend cap | **$20 a month, $5 a week**; a dry run aborts if its estimate exceeds the remaining weekly cap | owner set 2026-10-18 |
| Agent PR cap | 10 PRs a week; at most 5 auto-merges a day | recommended |
| Diff cap R0 | venues added + removed <= 2%; rows with a changed field <= 5% | recommended |
| Diff cap R1 | <= 25 rows | recommended |
| Diff cap R2 | <= 10 rows, raised to 20 after 100 accepted | recommended |
| Venue count drop | <= 1% for every class | recommended |
| N to earn auto-merge | R0: 6 PRs (about 3 months) plus 3 clean shadow runs; R1: 15; R2: 30 per field type | recommended |
| R2 precision bar | field precision >= 95% on >= 100 fields (ADR 0017's 90% stays the bar for triage use only) | recommended |
| Audit sample | 10% of auto-merged PRs, minimum 5 a week | recommended |
| Where agents run | extract/load/build/PR on the owner's machine (scheduled task); merge gate, audit digest and kill-switch check in GitHub Actions; alert if no refresh PR in 20 days; revisit by moving `data/raw` to object storage | recommended |

The earlier draft numbers in sections 3 and 4 (for example N = 20 for R0) are superseded by this table.

## Amends
- **ADR 0008:** "a reviewer checks the evidence, then merges" becomes "a reviewer or, for classes that have earned it, the merge gate". Confirmation levels and the two-source rule are unchanged.
- **ADR 0017:** "nothing applied without a person approving" becomes "nothing applied without a person or the merge gate approving", and only for fields past the precision bar.

## Not decided here
- **Where agents run.** Raw CSVs live in the main checkout (`data/raw`), extracts take about 15 minutes and read S3. Options: a scheduled local task on the owner's machine (works today, depends on it being on), GitHub Actions with raw data in object storage (more moving parts, always on), or a mix. Decide before stage 1.
- Link discovery or crawling beyond held URLs, PDFs and images, and unattended deletes of venues (each needs its own ADR).
- Any use of agents for the app code or the models. This ADR covers data PRs only.

## Consequences
- Owner review time shifts from approving each change to reading a weekly digest and handling R3 escalations. We expect most refresh PRs to need no review once R0/R1 earn it; R2 takes longer because it needs the reader and a precision measurement first.
- New work: the merge gate script, a scorecard no-regression check, a sport-name sync check, `docs/agent_log.csv`, branch protection with required checks, a bot token, the kill-switch variable, and the audit digest job.
- A wrong fact can now reach the map without a person seeing it first. We accept that only where measured precision is high, the change is easy to revert, and the digest samples it.
- This ADR does not start anything running. The first step is stage 0 with the cheap fixes listed in `docs/self_service_plan.md`.
