# Scheduled runs in the cloud (owner 2026-11-01)

The six scheduled tasks (`docs/tournament_run_parts.md` parts 1-5, search interest) also exist as cloud routines at https://claude.ai/code/routines, created **disabled**. A cloud run starts from a clean clone, so it has no raw data, no built-in browser, no `.env` and no local `gh` login.

| Routine | Cron (America/Los_Angeles) |
|---|---|
| Tournaments part 1-4 | 09:00, 10:30, 12:00, 13:30 on the 1st and 15th (each gated on the previous part, as before) |
| Data refresh part 5 | 15:00 on the 1st and 15th |
| Search interest | 10:00 on the 3rd of Jan/Apr/Jul/Oct |

**Raw data.** The gitignored `data/raw` CSVs live gzipped in the private repo `abov/courtconnect-data` (`raw/`; `overture_addresses.csv.gz` is split in `.partNN` chunks). Each routine has it as a second git source; `python ingestion/cloud_bootstrap.py` unpacks it into `data/raw`, installs `requirements.txt` and builds `courtconnect.duckdb`. After a local extract + load, refresh the data repo: gzip each file in `data/raw`, `split -b 80M -d overture_addresses.csv.gz overture_addresses.csv.gz.part`, commit, push.

**What differs from local runs** (the routine prompts say so; the docs stay written for the local run): no browser pane (ITF, Club Locker, padelusa, Instagram and Google Trends are read with WebFetch once, otherwise listed as "needs browser, not read"); no `.env` (sports sheet sync, form reports, GoatCounter not checked); no extract; if `gh` is not authenticated a part pushes its branch and puts the PR text in the session note, and Part 5 stops at its preflight.

**To switch over:** merge the PR that adds `cloud_bootstrap.py`; set the environment's network access to allow the sources (and a `GH_TOKEN` if you want PRs opened from cloud); Run now on part 1 to test; then enable the routines and disable the local tasks (a cloud and a local run on the same day would open two tournament PRs).
