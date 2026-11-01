# 2026-10-22 Snowflake removal check
Audit found the code removal already landed in #304 (2026-10-21): no `snowflake` in profiles, Makefile, `load_raw.py`, `requirements.txt`, `.env.example`, `infra/` or workflows; only `cross_db.sql`'s `adapter.dispatch` macros stay (ADR 0018). This PR fixes the last stale doc lines (ADR 0014 engines rule, `docs/case_study.md`, `docs/self_service_plan.md`, ADR 0018 consequences + status).
Next: nothing; Google place-ID layer left untouched (owner undecided).
