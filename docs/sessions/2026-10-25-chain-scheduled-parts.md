# 2026-10-25 Chain the scheduled parts

Parts 1-5 no longer run on separate days: Part 1 keeps the 09:00 cron on the 1st and 15th, and each part's last step starts the next (`run_scheduled_task`), so they run in order and never overlap. Parts 2-5 have no cron (placeholder 2099 date, approvals kept). Rules in `docs/tournament_run_parts.md`.
Next: the first real chain is 2026-11-01; check each part's summary for "NEXT PART NOT STARTED" (the trigger tool may not be available inside a scheduled session, in which case start the next part by hand).
