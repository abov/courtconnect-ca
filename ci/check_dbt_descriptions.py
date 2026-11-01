"""Fail when a dbt model or seed has no description, so the published dbt docs (/dbt-docs/) stay complete.

Run after `dbt build` or `dbt parse` (reads transform/target/manifest.json). Add the description to transform/models/schema.yml.
Column descriptions are not required: the docs site shows column names and types from the catalog, and only the keys carry tests.
"""
import json
import sys
from pathlib import Path

manifest = json.loads(Path("transform/target/manifest.json").read_text(encoding="utf-8"))
missing = sorted(
    f"{n['resource_type']} {n['name']}"
    for n in manifest["nodes"].values()
    if n["resource_type"] in ("model", "seed") and not (n.get("description") or "").strip()
)
if missing:
    sys.exit("No description in transform/models/schema.yml for:\n  " + "\n  ".join(missing))
print(f"dbt descriptions ok: every model and seed is documented ({sum(1 for n in manifest['nodes'].values() if n['resource_type'] in ('model', 'seed'))} checked)")
