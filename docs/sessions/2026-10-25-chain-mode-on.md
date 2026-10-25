# 2026-10-25 Chain mode back on

Owner added the `run_scheduled_task` allow rule. Run doc and README are back to chain mode (Part 1 on the cron, each part starts the next; Parts 2-5 have only a 2099 placeholder date). The merge gate merged refresh PR #410 end to end (comment, squash merge, pages dispatch), because the owner had already set `AGENT_AUTOMERGE_R0=true` and required reviews to 0.
Next: watch the first full chain test; if a part prints "NEXT PART NOT STARTED", restore staggered crons (09:00, 10:30, 12:00, 13:30, 15:00).
