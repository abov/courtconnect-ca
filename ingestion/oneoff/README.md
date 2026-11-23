# One-off scans

Research scripts that ran once (gym chains, city tennis directories, LA rec centres, the paddle-tennis map import, the aerial pilot, the beach-volleyball scan). They are not part of any `make` target or the monthly runbook; their results are already in the seeds or docs. Kept for reference and reruns: run from the repo root, e.g. `python ingestion/oneoff/scan_24hour.py`. `keyword_sport_sweep.py` is the OSM keyword sweep for every sport (Mexico and the US regions): `query` (slow, resumable), `diff` (hits with no pin for the sport), `emit` (tag-only `manual_venues.csv` rows).
