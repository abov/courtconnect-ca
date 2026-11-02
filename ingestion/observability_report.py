"""Build the Elementary data-observability report from the local warehouse (docs/data_observability.md).

    python ingestion/observability_report.py        (or: make observability)

Reads the tables dbt build writes into the `elementary` schema of courtconnect.duckdb (test results, run history, row-count and schema
snapshots: aggregates and column names, no venue rows) and writes observability/elementary_report.html (git-ignored). Uses the separate
.venv-edr (next to the main .venv, so its path stays short: Windows' 260-character limit breaks the CLI's own dbt packages inside a deep
worktree path) because the CLI pins its own dbt version; set it up once with:
    python -m venv <main checkout>/.venv-edr && <main checkout>/.venv-edr/Scripts/pip install "elementary-data[duckdb]" "duckdb<2"
Anonymous usage tracking is off (transform/edr_config/config.yml). Run `make build` first; build closes the db file, so nothing else may have it open.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "observability" / "elementary_report.html"


def main() -> None:
    venv = Path(sys.executable).parents[1].parent / ".venv-edr"   # the main checkout's venv folder is shared by its worktrees
    exe = venv / ("Scripts/edr.exe" if sys.platform == "win32" else "bin/edr")
    if not exe.exists():
        sys.exit(f"No Elementary CLI at {venv}. Create it:  python -m venv {venv} && {venv}/Scripts/pip install \"elementary-data[duckdb]\" \"duckdb<2\"")
    OUT.parent.mkdir(exist_ok=True)
    subprocess.run([str(exe), "report", "--project-dir", "transform", "--profiles-dir", "transform", "--config-dir", "transform/edr_config",
                    "--target-path", "observability/edr_target", "--file-path", str(OUT), "--open-browser", "false"], cwd=ROOT, check=True,
                   env={**os.environ, "COURTCONNECT_DB": str(ROOT / "courtconnect.duckdb")})
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
