# 2026-10-29 beta questions, change feed, player-finding plan
- Added beta questions 8-11 (player finding, related-sport card, change emails, cost tier) to `docs/feedback_round.md`; wrote `docs/player_finding_plan.md` (plan only).
- Built the public change feed (ADR 0025 step 1): `ingestion/build_changes.py`, `app/data/changes.json` (seeded with the Oct refresh diff), `make changes`, runbook 8a, CI `--check`. Venue ids are stable (1 drift of 10,279).
- Next: ADR 0026 OSM snapshot diff feeds this; a "What's new" strip only if the beta asks.
