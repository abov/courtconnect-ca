# 2026-10-18 community reports: popup link + make sync-reports

Built the rest of step 3: the popup's "Report without a GitHub account" link (prefilled Google Form) and `make sync-reports` (`ci/sync_reports.py`, shares `process()` with `ci/issue_to_pr.py`; reads `REPORTS_CSV_URL`). Tested on a sample CSV and a full build; also fixed lead rows that were one column short.
Next: owner adds `REPORTS_CSV_URL` to `.env` (link in the shared notes), then the first real run at the next sync (runbook 2b). Reports on a pin only count as `reported` until two reporters or an official page back them.
