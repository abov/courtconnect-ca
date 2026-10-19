# 2026-10-18: ADR 0019 stage 0 cleanup

Added `ci/check_scorecard_regression.py` (ADR 0019 gate 4) and `ci/check_sport_names.py` (sheet vs counts vs seed sport names), wired both into `docs/monthly_refresh.md`, and removed the Snowflake lines from the runbook. Neither check is in `ci.yml` yet.
Finding: the scorecard check flags the latest trend line (venues 10,466 -> 10,230, -2.3%, from the 2026-10-17/18 match-rule merges); explain it in the next refresh PR. Next: decide whether to run the checks in CI, then the draft-mode `refresh` agent (owner OK needed to schedule).
