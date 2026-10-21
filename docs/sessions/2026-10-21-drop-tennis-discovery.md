# 2026-10-21 Drop tennis visibility + "Try something new"; code cleanup
- Owner dropped roadmap item 7b (ADR 0015 amendment). Cleanup in the same PR: one shared `ingestion/useragent.py` (4 scripts sent a non-project User-Agent, 2 a Mozilla string); 8 one-time scans moved to `ingestion/oneoff/`; Snowflake code removed early (ADR 0018 amendment). Full dbt build 280 PASS, all CI checks pass locally.
- Next: none from this session. Any new outside request should import `useragent.HEADERS`.
