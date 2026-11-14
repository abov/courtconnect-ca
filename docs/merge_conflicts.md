# Fewer merge conflicts

Parallel region sessions all touch the same few files. What cuts the collisions (2026-11-13):

- **`app/data/venues.json` is one record per line** (`dump_lines` in `ingestion/export_app_data.py`), sorted by lat, lon, id. Git merges edits to different venues by itself. Line 1 is `meta` (counts and date).
- **Merge driver `venues`** (`ingestion/merge_venues.py`): merges the record lines, then rebuilds `meta` as ours + theirs - base. Still run `dbt build`, `make app-data` and `ci/check_export_fresh.py` before shipping. On a real conflict the old rule holds: take main's copy, rebuild, re-export.
- **`merge=union`** (`.gitattributes`) for append-only logs and seeds (the scan docs, ADR 0034, `manual_venues`, `venue_leads`, `venue_actions`, `venue_court_counts`, `watch_events`, `social_events`, `player_groups`, `event_sources.csv`): two PRs adding lines at the same spot keep both. The cost: if both PRs edited the same row you get two versions, and the dbt unique tests fail on the key. Delete the stale one.
- **`rerere`**: git replays a conflict resolution it has seen before (rebasing the same branch again).
- **Once per clone** (worktrees share it): `python ingestion/setup_git.py` sets the hooks path, rerere and the driver. Without it git does a plain text merge.
- **Habits**: land small and often; rebase on `origin/main` right before opening and before merging; add new rows near related ones, not always at the end of the file.
- A change that shifts the `sports` list order renumbers every venue's sport index, so every venue line changes. Add new sports at the end of the list and expect one conflict-prone PR when you must reorder.
