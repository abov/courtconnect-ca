"""Set up a fresh cloud checkout (scheduled routines, docs/cloud_routines.md): deps, raw CSVs, courtconnect.duckdb.

The raw extract CSVs are gitignored (655 MB), so cloud sessions get them from the private repo abov/courtconnect-data
(gzipped, `overture_addresses.csv.gz` split in `.partNN` chunks), added to the routine as a second git source.

    python ingestion/cloud_bootstrap.py [--data-repo PATH] [--no-build]

Finds the data repo from --data-repo, $COURTCONNECT_DATA_REPO, or a sibling/child folder named courtconnect-data;
unpacks it into the default raw folder (ingestion/rawdir.py, so no env var is needed afterwards); installs
requirements.txt if dbt is missing; then runs ingestion/fresh_db.py (~1-2 min) unless --no-build.
"""
from __future__ import annotations

import argparse
import gzip
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

from rawdir import ROOT, raw_dir


def find_data_repo(arg: str | None) -> Path:
    cands = [arg, os.environ.get("COURTCONNECT_DATA_REPO")]
    for base in (ROOT.parent, ROOT, Path.home(), Path("/workspace"), Path("/home/user")):
        cands.append(str(base / "courtconnect-data"))
    for c in cands:
        if c and (Path(c) / "raw").is_dir():
            return Path(c) / "raw"
    sys.exit("courtconnect-data not found: add abov/courtconnect-data as a second git source, or pass --data-repo PATH")


def unpack(src: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    names = sorted({p.name.split(".gz")[0] for p in src.glob("*.gz*")})
    for name in names:
        parts = sorted(src.glob(name + ".gz*"))  # one file, or .part00 .part01 ... in order
        # chunks are byte slices of ONE gzip stream: concatenate, then decompress
        with open(dest / (name + ".gz.tmp"), "wb") as tmp:
            for part in parts:
                with open(part, "rb") as raw:
                    shutil.copyfileobj(raw, tmp)
        with gzip.open(dest / (name + ".gz.tmp"), "rb") as zin, open(dest / name, "wb") as out:
            shutil.copyfileobj(zin, out)
        (dest / (name + ".gz.tmp")).unlink()
        print(f"  {name}: {(dest / name).stat().st_size / 1e6:.1f} MB")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-repo")
    ap.add_argument("--no-build", action="store_true")
    a = ap.parse_args()

    src, dest = find_data_repo(a.data_repo), raw_dir()
    print(f"unpacking {src} -> {dest}")
    unpack(src, dest)

    if importlib.util.find_spec("dbt") is None:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(ROOT / "requirements.txt")], check=True)
    if not a.no_build:
        subprocess.run([sys.executable, str(ROOT / "ingestion" / "fresh_db.py")], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
