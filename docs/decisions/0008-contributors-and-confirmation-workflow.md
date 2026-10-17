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
- An in-app reviewer queue with sign-in. Only worth building once GitHub review becomes the bottleneck.

## Update 2026-10-11: Suggest a change
- Every venue popup has a **Suggest a change** link that opens the `suggest-a-change` issue form with the venue prefilled.
- A reviewer adds the `approved` label. `.github/workflows/issue-to-pr.yml` runs `ci/issue_to_pr.py`, which appends ONE row and opens a
  pull request: a link-out (`venue_actions`) or a confirmation (`venue_confirmations`) when the name and city match a row in
  `manual_venues`, otherwise a lead (`venue_leads`). Overture/OSM venues therefore become leads until a reviewer places them.
  Issue text is untrusted: it is written only through the csv module, links must be https, and it never reaches a shell.
- `ci/check_seed_evidence.py` runs first in CI: every hand-edited row needs its evidence and a date (a `reported` venue needs
  evidence only), and links must be https. Two older rows are grandfathered in the script.
- Pushes made with `GITHUB_TOKEN` do not start CI, so the action starts `ci.yml` by `workflow_dispatch` on the new branch so the required
  `dbt-build` check reports. Untested until the first real issue; if the check does not appear, use a fine-grained token instead.

## Update 2026-10-16: community reports (word of mouth)
- The suggest-a-change form has **Report a racket sport played here** and a **Sport played here** field. No link is needed: the owner cannot
  visit venues, so what users saw or were told counts at the `reported` level, labelled "Reported, not independently confirmed".
- A report or confirmation on any map pin (not only `manual_venues`) becomes a `manual_venues` row at the pin's coordinates
  (`location_precision` = `pin: map id ...`, `confirmation` = `reported`) that the build merges onto that pin, plus the reporter's
  `venue_confirmations` row (`method` = `reported`). Later reports on the same pin reuse that row's `venue_key`.
- Corrections and closures still become leads: one unverified report never removes or changes a venue.
- Reported rows are not counted as confirmations on the map. Raising a level still needs a reviewer (two independent people, or a
  report plus an official page). Plan and next steps (report count, no-GitHub form): `docs/community_reports_plan.md`.
