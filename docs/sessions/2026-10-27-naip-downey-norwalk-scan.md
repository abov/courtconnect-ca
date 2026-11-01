# 2026-10-27 NAIP rescans (Downey/Norwalk, Elk Grove)

- Rebuilt the Hawthorne-trained model and scanned Downey/Norwalk (LA model, no tuning): recall 0.82 vs OSM, 12 candidates on no OSM pitch; the 3 in parks/schools were a pool, a duplicate of Downey Tennis Center and an unconfirmable Santa Fe High court row. None added.
- `ingestion/oneoff/aerial_pilot.py` now handles UTM 10N/11N, regional training (`--train`, `--init`), `--context-only`, recall by sport, and a correct `nearest_osm_court_m`. Elk Grove (zone 10N): LA model recall 0.27, fine-tuned 0.29, pickleball ~0/14; its 2 park/school candidates were a roof and a pool.
- Verdict: stop rule hit, do not scale; results in `docs/ml_plan.md`. Next: none for imagery unless a model that sees pickleball lines appears; use city pages and reports.
