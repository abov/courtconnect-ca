# Token efficiency

Why: Claude Code re-reads the whole conversation and `CLAUDE.md` every turn, so cost is driven by session length and always-loaded text, not by the work (`ops_metrics.md`, 2026-11-14: cache re-reads dominate; heaviest sessions peaked at 200-330k context). Added 2026-11-17.

## What enforces it
- `CLAUDE.md` is kept short; long procedures live in [`working_practices.md`](working_practices.md) and [`commands.md`](commands.md) and are read only when needed.
- `.claude/hooks/guard.py` (wired in `.claude/settings.json`, tested by `python ci/test_guard_hook.py`):
  - **deny**: reading or editing `.env`; whole-file reads of `app/data/venues.json`, `*.duckdb`, `transform/target`, `transform/logs`, and of `app/index.html` without a line range.
  - **ask**: reading images, taking browser screenshots (the owner can still say yes).
  - **warn**: once the session transcript passes ~800 KB (about 150k tokens of history, repeated every +400 KB), the model is told to hand off and suggest a fresh session. Tune with `CC_GUARD_WARN_KB` and `CC_GUARD_REPEAT_KB`.
  - Fails open: a bug in the hook never blocks work.
- `.rgignore` keeps generated files out of Grep results.

## Changing it
Add a rule to `guard.py` and a case to `ci/test_guard_hook.py`; keep the matching sentence in `CLAUDE.md` to one line. Hook changes load at the next session start. Bigger levers (not done here): stop committing `venues.json` (scoped 2026-11-17: needs raw data in CI, not cheap), script the repeated research passes, exception-queue routines (see `status.md`).
