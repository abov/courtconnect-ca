"""Build courtconnect.duckdb from scratch in this checkout: load the shared raw CSVs, then run the full dbt build.

A new git worktree has no database. Instead of copying one from another checkout (it may be stale or from another
branch), run:

    python ingestion/fresh_db.py

It loads data/raw (the shared folder, see rawdir.py; the same one for every worktree) and builds seeds, models and tests
with this branch's seeds, so the result matches this branch. About a minute, mostly the address rows.
"""
from __future__ import annotations

import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


PKG_DIR = ROOT / "transform" / "dbt_packages"


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "courtconnect-ca/0.1 (+https://github.com/abov/courtconnect-ca)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def _vtuple(v: str) -> tuple:
    return tuple(int(x) if x.isdigit() else 0 for x in re.split(r"[.\-]", v))


def _pick_version(spec, available: list[str]) -> str:
    """Highest hub version satisfying an exact string or a list of >=,<=,>,<,= bounds."""
    bounds = [spec] if isinstance(spec, str) else list(spec)
    ok = []
    for v in available:
        if "-" in v:   # skip prereleases
            continue
        good = True
        for b in bounds:
            m = re.match(r"\s*(>=|<=|>|<|=)?\s*(\S+)", str(b))
            op, ref = (m.group(1) or "="), m.group(2)
            a, r = _vtuple(v), _vtuple(ref)
            good &= {">=": a >= r, "<=": a <= r, ">": a > r, "<": a < r, "=": a == r}[op]
        if good:
            ok.append(v)
    if not ok:
        raise RuntimeError(f"no hub version satisfies {spec}")
    return max(ok, key=_vtuple)


def _install_hub_packages(packages_yml: Path, seen: set[str]) -> None:
    """Fallback for `dbt deps` (sandbox proxies block codeload.github.com): fetch hub tarballs by hand."""
    import yaml
    for entry in (yaml.safe_load(packages_yml.read_text()) or {}).get("packages", []):
        pkg = entry.get("package")
        if not pkg or pkg in seen:
            continue
        seen.add(pkg)
        meta = json.loads(_get(f"https://hub.getdbt.com/api/v1/{pkg}.json"))
        versions = meta["versions"]
        v = _pick_version(entry["version"], list(versions))
        url = versions[v]["downloads"]["hub"]["tarball"]
        print(f"deps fallback: {pkg} {v} <- {url}")
        with tempfile.TemporaryDirectory() as tmp:
            with tarfile.open(fileobj=io.BytesIO(_get(url)), mode="r:gz") as tf:
                tf.extractall(tmp, filter="data")
            root = next(Path(tmp).iterdir())
            name = re.search(r"^name:\s*['\"]?([\w]+)", (root / "dbt_project.yml").read_text(), re.M).group(1)
            dest = PKG_DIR / name
            shutil.rmtree(dest, ignore_errors=True)
            PKG_DIR.mkdir(parents=True, exist_ok=True)
            shutil.move(str(root), str(dest))
        if (dest / "packages.yml").exists():   # transitive packages (elementary needs dbt_utils)
            _install_hub_packages(dest / "packages.yml", seen)


def install_packages(dbt: list[str]) -> None:
    """`dbt deps`; if it fails (it also wipes dbt_packages), install the hub tarballs by hand. Local path unchanged."""
    args = ["--project-dir", "transform", "--profiles-dir", "transform"]
    if subprocess.run(dbt + ["deps"] + args, cwd=ROOT).returncode == 0:
        return
    print("dbt deps failed; falling back to dbt hub tarballs (docs/cloud_routines.md)")
    _install_hub_packages(ROOT / "transform" / "packages.yml", set())


def main() -> None:
    py = sys.executable
    subprocess.run([py, str(ROOT / "ingestion" / "load_raw.py")], cwd=ROOT, check=True)   # the shrink guard still protects an existing db
    exe = Path(py).parent / ("dbt.exe" if sys.platform == "win32" else "dbt")
    dbt = [str(exe)] if exe.exists() else [py, "-m", "dbt.cli.main"]
    install_packages(dbt)   # packages (Elementary); never re-run deps after this, it would wipe the fallback install
    subprocess.run(dbt + ["build", "--project-dir", "transform", "--profiles-dir", "transform", "--full-refresh"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
