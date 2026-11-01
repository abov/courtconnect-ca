# 2026-10-27: fork guide and region config

Moved the CA/NV regions, metro boxes and `--area` names into `ingestion/regions.json` (same values as before, checked against the old code; `ci/check_regions.py` passes); added `COURTCONNECT_USER_AGENT` override and `docs/fork_guide.md`.
Next: try a real fork build on a small area, then fix the leftovers listed in the guide (`ask.py`, coverage report text, US-only Census steps). Not done: PR not opened, `dbt build` not run (no transform change).
