# 2026-10-24 Split the scheduled runs

The "Run now" of `courtconnect-tournament-refresh` read one source and stopped (too big for one session at the low-usage settings). Split into five tasks, 1st-5th and 15th-19th at 09:00, all steps in `docs/tournament_run_parts.md` (tasks just point at it); parts 1-4 share one tournament PR per cycle, Part 5 is the data refresh stacked on it.
Next: after merging, "Run now" Part 2 (or wait for 11-01) and check it reads every source; watch total spend against ADR 0019's $20 a month.
