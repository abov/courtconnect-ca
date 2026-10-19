# 2026-10-19 sync-reports: CI test, dry run, email/phone screen

PR #238 (another session) landed the popup link and `make sync-reports` while this session built the same thing; this one was closed (#239) and only the gaps were added on top: `ci/test_sync_reports.py` with `ci/fixtures/reports_*` (runs in CI, no network), `make sync-reports ARGS=--dry-run` (writes into a throwaway copy of the seeds), and a screen that rejects rows containing an email address or phone number. Real dry run against the published `approved` tab: 0 approved rows (the tab publishes empty until the owner approves a row).
Next (owner): add `REPORTS_CSV_URL` to `.env`, delete the TEST row in the sheet, approve one real test report, dry-run, then run at the next sync (runbook 2b).
