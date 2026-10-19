# 2026-10-19 community reports: popup link + make sync-reports

Built step 3 of `docs/community_reports_plan.md`. Popup (Details, sources and corrections) now has "Report a change without GitHub": the Google Form with Venue name, City and Map ID prefilled (https, new tab, `rel=noopener`; GoatCounter event `report-form`). `ingestion/sync_reports.py` (`make sync-reports ARGS=--dry-run`) reads the published `approved` tab CSV (`REPORTS_CSV_URL` in `.env`), skips rows whose `form:<timestamp digits>` id is already in a seed, skips rows with email/phone/non-https links, and writes the rest through the new shared `apply_report()` in `ci/issue_to_pr.py` (refactor, issue flow unchanged). Test: `ci/test_sync_reports.py` + `ci/fixtures/reports_*` (in CI, no network). Real dry run today: 0 approved rows.

Next (owner): add `REPORTS_CSV_URL` to `.env`, delete the TEST row in the sheet, send a real test report and mark it `approved`, then dry-run. No seeds or `venues.json` changed.
