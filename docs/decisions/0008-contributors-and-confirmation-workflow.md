# 0008. Contributors and the confirmation workflow

Date: 2026-10-10. Status: accepted.

## Context
One person cannot visit or verify venues across California. We want trusted helpers to confirm venues, and the public to report
them, without building accounts or a backend, and without weakening the confirmation levels from ADR 0007.

## Decision
- **Three roles, all handled by GitHub.**
  - *Public:* submits the "Report a venue" or "Confirm a venue" issue forms. No account of ours is needed, only a GitHub login.
  - *Contributor:* opens a pull request that edits seeds. Cannot merge.
  - *Reviewer:* GitHub collaborator with merge rights. Checks the evidence, then merges. Added and removed by the owner.
- **Data still changes only in seeds** (`manual_venues`, `venue_actions`, `venue_leads`, and so on), so every change is reviewed,
  diffed and reversible. Never `all_racquet.csv`.
- **A confirmation needs evidence.** `visited` needs a date and what was seen; `official` needs the operator's or a government
  page; `reported` is the floor. Nothing is raised a level without a source a reviewer can open.
- **Public pages only.** Contributors must not use or share anyone's logins, and must not paste content from sites whose terms
  forbid storing it (ADR 0005, ADR 0007). Link to it instead.
- **Personal information stays out** of the repo and of issue forms. Contributors are credited by GitHub handle in git history.
- **Two independent confirmations** (different people, or a visit plus an official page) are what justify raising a venue from
  `reported` to `official` or `visited`. A single report never does.

## Not built yet
- `confirmed_by` (a GitHub handle) and a confirmation count on `manual_venues`, shown on the map. This changes models and the app,
  so it gets its own step and a `make build`.
- A CI check that fails a pull request when a confirmed row lacks `evidence` or a date.
- An in-app reviewer queue with sign-in. Only worth building once GitHub review becomes the bottleneck.
