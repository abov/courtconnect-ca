# Scheduled runs in the cloud (owner 2026-11-01; live 2026-11-02)

The twice-monthly chain and the quarterly search-interest refresh run as cloud routines at https://claude.ai/code/routines. They are **enabled** and the local scheduled tasks were deleted by the owner on 2026-11-02, so these are the only copies (a local and a cloud run on the same day would open two tournament PRs). A cloud run starts from a clean clone, so it has no raw data, no built-in browser, no `.env` and no local `gh` login.

| Routine | id | Cron (America/Los_Angeles) |
|---|---|---|
| CourtConnect tournaments part 1: tennis, pickleball, ITF | `trig_01AqJ2ucA3oqAB5oN9icwLE7` | 09:00 on the 1st and 15th |
| CourtConnect tournaments part 2: badminton, table tennis, squash | `trig_01KR5SqAcLwkoLWfpEd6jDYL` | 10:30 on the 1st and 15th |
| CourtConnect tournaments part 3: padel, beach tennis, lead rechecks | `trig_018RipCVXWnJ9y55YnpUFJsU` | 12:00 on the 1st and 15th |
| CourtConnect tournaments part 4: Instagram sweep, player groups, new courts | `trig_01Bzo6g8B6YffCqx1buxkwwV` | 13:30 on the 1st and 15th |
| CourtConnect data refresh: part 5 | `trig_019asuxbJ84AxduTtuecxe45` | 15:00 on the 1st and 15th |
| CourtConnect search interest refresh (quarterly) | `trig_017bYuYYqZ62ysVfTjs68FXN` | 10:00 on the 3rd of Jan/Apr/Jul/Oct |

Each part is gated on the one before it (`docs/tournament_run_parts.md`). Retired local tasks: `courtconnect-refresh` (merged into Part 5) and `courtconnect-squash-club-locker` (now inside Part 2). A dead-man's switch (`.github/workflows/refresh-watchdog.yml`) fails on the 2nd and 16th if no "Tournaments" PR was opened.

**Raw data.** The gitignored `data/raw` CSVs live gzipped in the private repo `abov/courtconnect-data` (`raw/`; `overture_addresses.csv.gz` is split in `.partNN` chunks). Each routine has it as a second git source; `python ingestion/cloud_bootstrap.py` unpacks it into `data/raw`, installs `requirements.txt` and builds `courtconnect.duckdb`. After a local extract + load, refresh the data repo: gzip each file in `data/raw`, `split -b 80M -d overture_addresses.csv.gz overture_addresses.csv.gz.part`, commit, push.

**What differs from local runs** (the routine prompts say so; the docs stay written for the local run): no browser pane (ITF, Club Locker, padelusa, Instagram, Google Trends and reddit.com are read with WebFetch once, otherwise listed as "needs browser, not read"); no `.env` (sports sheet sync, form reports, GoatCounter not checked); no extract; if `gh` is not authenticated a part pushes its branch and puts the PR text in the session note, and Part 5 stops at its preflight.

**To change a routine:** edit the steps in `docs/tournament_run_parts.md` / `docs/refresh_agent.md` on `main` (the prompts read them at run time); edit a routine's own prompt, cron or enabled flag only at claude.ai/code/routines. Run now on a part to retest it.
