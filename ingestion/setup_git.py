"""One-time git setup per clone (worktrees share it): hooks, conflict-memory, and the venues.json merge driver.

    python ingestion/setup_git.py

- core.hooksPath .githooks   pre-push: rebase check + cheap CI checks
- rerere.enabled true        git remembers how you resolved a conflict and replays it on the next rebase
- merge driver "venues"      app/data/venues.json merges by line, meta counts by arithmetic (ingestion/merge_venues.py)
The `merge=union` rules for append-only logs and seeds are in .gitattributes and need no setup.
"""
import subprocess

SETTINGS = [
    ("core.hooksPath", ".githooks"),
    ("rerere.enabled", "true"),
    ("merge.venues.name", "venues.json: line merge + meta arithmetic"),
    ("merge.venues.driver", "python ingestion/merge_venues.py %O %A %B"),
]

for key, value in SETTINGS:
    subprocess.run(["git", "config", key, value], check=True)
    print(f"git config {key} = {value}")
