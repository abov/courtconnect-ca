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
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
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


HUB = "https://hub.getdbt.com/api/v1/{}.json"
PKG_DIR = ROOT / "transform" / "dbt_packages"


def _get(url: str, tries: int = 3) -> bytes:
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "courtconnect-ca/0.1 (+https://github.com/abov/courtconnect-ca)"})
            with urllib.request.urlopen(req, timeout=60) as r:  # honours HTTPS_PROXY and SSL_CERT_FILE; TLS stays verified
                return r.read()
        except Exception as e:  # noqa: BLE001
            if i == tries - 1:
                raise
            print(f"  retry {url}: {e}")
            time.sleep(2 ** i)
    raise AssertionError


def hub_install(spec: str, version: str, dest: Path) -> None:
    """Fetch one package from the dbt hub CDN (public.cdn.getdbt.com), check its sha1, unpack into dest/<name>."""
    info = json.loads(_get(HUB.format(spec)))["versions"][version]
    body = _get(info["downloads"]["hub"]["tarball"])
    if hashlib.sha1(body).hexdigest() != info["downloads"]["sha1"]:
        sys.exit(f"{spec} {version}: sha1 mismatch")
    name = info["name"]
    with tarfile.open(fileobj=io.BytesIO(body)) as tf:
        top = tf.getnames()[0].split("/")[0]
        tf.extractall(dest, filter="data")
    shutil.rmtree(dest / name, ignore_errors=True)
    (dest / top).rename(dest / name)
    print(f"  {spec} {version} -> {dest / name}")


def install_dbt_packages() -> None:
    """`dbt deps`, with a hub-CDN fallback.

    In the cloud sandbox the proxy answers the codeload.github.com / github.com archive URLs that dbt deps downloads with a
    403 JSON body unless that repo is attached to the session; dbt reports it as "not a gzip file". hub.getdbt.com and
    public.cdn.getdbt.com are reachable, so install the versions pinned in transform/package-lock.yml from there.
    """
    dbt = [sys.executable, "-m", "dbt.cli.main", "deps", "--project-dir", "transform", "--profiles-dir", "transform"]
    for _ in range(2):
        if subprocess.run(dbt, cwd=ROOT).returncode == 0:
            return
        time.sleep(3)
    print("dbt deps failed; installing the pinned packages from the dbt hub CDN")
    import yaml  # installed with dbt-core
    lock = yaml.safe_load((ROOT / "transform" / "package-lock.yml").read_text())["packages"]
    PKG_DIR.mkdir(exist_ok=True)
    for p in lock:
        hub_install(p["package"], str(p["version"]), PKG_DIR)


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
    install_dbt_packages()
    if not a.no_build:
        subprocess.run([sys.executable, str(ROOT / "ingestion" / "fresh_db.py")], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
