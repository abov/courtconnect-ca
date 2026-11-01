# 2026-10-28 Planet-scale benchmark

Added `ingestion/oneoff/overture_scale_benchmark.py` and ran it on Overture `2026-10-21.0`: the places and address extracts fetch about 2% of their themes (`docs/planet_scale_benchmark.md`, plan in `docs/planet_scale_plan.md`); README has one "Scale" paragraph.
Next, only if wanted: OSM minutely replication diffs -> `app/data/changes.json` (needs its own ADR), then an Overture release-to-release diff.
