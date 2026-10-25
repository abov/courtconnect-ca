# 2026-10-25 README: the scheduled chain

README "Workflow and automation" now describes the five chained agent runs (one session each, no subagents), and the roadmap item is "prove the chain end to end". First chain test (Part 1 started by hand): Part 1 finished in 9 min but could not start Part 2 unattended (the trigger needs an approval or an allow rule for `mcp__scheduled-tasks__run_scheduled_task`); noted in `docs/tournament_run_parts.md`.
Next: owner adds the allow rule, then re-test; until then start each part by hand.
