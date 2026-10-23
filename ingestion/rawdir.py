"""One shared folder for the extracted raw CSVs, so every git worktree reads and writes the same data.

Worktrees (.claude/worktrees/*) used to each hold their own data/raw, which went stale and had to be copied by hand
(a reload from an old copy once cut 888 walls to 263). Now every script resolves its default data folder here:

    1. $COURTCONNECT_DATA_DIR, if set (any folder);
    2. else <main checkout>/data/raw, found through git's common dir, so a worktree uses the main checkout's folder;
    3. else <this repo>/data/raw (no git, or a plain clone: same as before).

CI passes --data-dir ci/fixtures explicitly and is unaffected. Run `python ingestion/rawdir.py` to print the folder.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def raw_dir() -> Path:
    env = os.environ.get("COURTCONNECT_DATA_DIR")
    if env:
        return Path(env)
    try:
        out = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=ROOT, capture_output=True, text=True,
                             timeout=10, check=True).stdout.strip()
        common = (ROOT / out).resolve()
        if common.name == ".git":
            return common.parent / "data" / "raw"
    except (OSError, subprocess.SubprocessError):
        pass
    return ROOT / "data" / "raw"


def raw_path(name: str) -> str:
    """Default location of one raw file, as a forward-slash string (safe inside DuckDB SQL on Windows)."""
    return (raw_dir() / name).as_posix()


if __name__ == "__main__":
    print(raw_dir().as_posix())
