"""Build courtconnect.duckdb from scratch in this checkout: load the shared raw CSVs, then run the full dbt build.

A new git worktree has no database. Instead of copying one from another checkout (it may be stale or from another
branch), run:

    python ingestion/fresh_db.py

It loads data/raw (the shared folder, see rawdir.py; the same one for every worktree) and builds seeds, models and tests
with this branch's seeds, so the result matches this branch. About a minute, mostly the address rows.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    py = sys.executable
    subprocess.run([py, str(ROOT / "ingestion" / "load_raw.py")], cwd=ROOT, check=True)   # the shrink guard still protects an existing db
    exe = Path(py).parent / ("dbt.exe" if sys.platform == "win32" else "dbt")
    dbt = [str(exe)] if exe.exists() else [py, "-m", "dbt.cli.main"]
    subprocess.run(dbt + ["build", "--project-dir", "transform", "--profiles-dir", "transform", "--full-refresh"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
