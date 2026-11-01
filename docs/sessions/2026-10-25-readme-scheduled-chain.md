# 2026-10-25 README: the scheduled chain

README "Workflow and automation" now describes the five chained agent runs (one session each, no subagents), and the roadmap item is "prove the chain end to end". First chain test (Part 1 started by hand): Part 1 finished in 9 min but could not start Part 2 unattended (the trigger needs an approval or an allow rule for `mcp__scheduled-tasks__run_scheduled_task`); noted in `docs/tournament_run_parts.md`.
Interim (owner OK): Parts 2-5 are back on their own crons on the 1st and 15th at 10:30, 12:00, 13:30 and 15:00 (Part 1 at 09:00), and the start-the-next step is skipped while they have crons. To make it self-running: owner adds the allow rule, then Parts 2-5 lose their crons; also wanted: a failure alert and the ADR 0019 auto-merge classes.
