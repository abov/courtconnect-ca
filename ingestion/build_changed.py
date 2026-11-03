"""dbt build of only what changed since the last good build (plus everything downstream), with a full-build fallback.

    python ingestion/build_changed.py            # state:modified+ against transform/.state, or a full build when there is none
    python ingestion/build_changed.py --full     # full build, then save the state
    python ingestion/build_changed.py --dry-run  # list what would be built (dbt ls), build nothing

After a successful build the run saves transform/target/manifest.json to transform/.state/ (git-ignored); the next run compares
the project files with it. Good for edits to seeds, models, macros and tests. It cannot see raw data: dbt does not know that
`make load` / an extract changed raw.* tables, so after loading raw data (a new state, a refresh) run --full.
CI always runs the full build; run --full (or `dbt build`) once before opening a PR. Run `dbt deps` once per checkout first.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "transform" / ".state"
MANIFEST = ROOT / "transform" / "target" / "manifest.json"
DBT_OPTS = ["--project-dir", "transform", "--profiles-dir", "transform"]   # dbt takes these after the subcommand


def run(args: list[str]) -> int:
    print("+", " ".join(args), flush=True)
    return subprocess.call(args, cwd=ROOT)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--full", action="store_true", help="ignore the saved state and build everything")
    ap.add_argument("--dry-run", action="store_true", help="only list the selected nodes")
    args = ap.parse_args()

    incremental = (STATE / "manifest.json").exists() and not args.full
    sel = ["--select", "state:modified+", "--state", str(STATE)] if incremental else []
    if not incremental:
        print("No saved state (or --full): full build." if not args.full else "--full: full build.")
    if args.dry_run:
        return run(["dbt", "ls", *DBT_OPTS, *sel])
    code = run(["dbt", "build", *DBT_OPTS, *sel])
    if code != 0:
        print("Build failed: the saved state was left as it was.")
        return code
    if MANIFEST.exists():
        STATE.mkdir(parents=True, exist_ok=True)
        shutil.copy2(MANIFEST, STATE / "manifest.json")
        print(f"Saved {STATE.relative_to(ROOT)}/manifest.json for the next run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
