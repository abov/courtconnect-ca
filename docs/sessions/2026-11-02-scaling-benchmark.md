# 2026-11-02 scaling benchmark
Added `ingestion/bench_scale.py` and `docs/scaling.md`: 1x/3x/10x raw data takes dbt 2.2 / 15 / 158 min (about quadratic), memory stays under 15 GB.
Next: profile `int_court_parent` and `int_venue_address`, add grid bucketing, rerun at 3x; then optional Elementary for data monitoring.
