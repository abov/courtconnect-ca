# Live agent activity (`make agent-activity`, added 2026-11-14)

A local page that shows what every Claude Code session on this machine is doing right now. Answers "is anything running, what is it touching, and is it failing?" without opening each session. Complements [`ops_metrics.md`](ops_metrics.md) (after-the-fact delivery numbers) and [`data_observability.md`](data_observability.md) (data health).

```bash
python ingestion/agent_activity.py                      # then open http://127.0.0.1:8766
python ingestion/agent_activity.py --hours 24 --port 9000 --all-projects
```

## What you see
- **Session cards**: state (active under 90 s since the last event, idle under 15 min, else done), turns, tool calls, errors, peak context (the "start a fresh session" signal in `CLAUDE.md`), top tools. Click a card to filter the feed to that session.
- **Feed**: newest tool calls first with time, tool, short target (file, command, search pattern, web host), how long it took and a red mark when the call failed. A call shows "…" until its result arrives. Pause freezes the view.

## How it works and what it never shows
- Tails `~/.claude/projects/*courtconnect*/**/*.jsonl` (the logs Claude Code already writes) once a second and polls from the page every 2 s. Python standard library only; nothing to install.
- Local and read-only: binds to 127.0.0.1, writes nothing, sends nothing anywhere.
- Shows tool names and short targets only, never prompts, replies or file contents. Secret-looking values in commands are masked and `.env` shows as `[env]`.

## Limits
- Only this machine's sessions: cloud routines (`docs/cloud_routines.md`) and other computers write no logs here.
- It shows a call when the log line is written, so a tool that is still running shows "…"; a very long call can look stuck.
- Masking is pattern-based; it is a safety net, not a guarantee. Do not expose the port beyond localhost.
