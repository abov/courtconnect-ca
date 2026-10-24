# 2026-10-24 R2 event tracking

Added `docs/r2_seen.csv` (one row per R2 Sports TID with a decision) and `ci/check_r2_events.py` (CI: R2-sourced watch events must link their own TID page and match the log; `pending` rows only remind). Added the "Report a tournament or event" issue form (`event-report`), a link under the Watch list, and event handling in `make issues`.
Next: read R2 TIDs 54262 and 54415 in the browser pane (this cloud session cannot reach r2sports.com), set their decision and add the watch event if in region; fill TIDs for the 3 grandfathered racquetball rows and empty `GRANDFATHERED` in the check.
