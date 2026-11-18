"""Refresh the private data repo abov/courtconnect-data from the shared raw folder (one command after extract + load).

    python ingestion/push_data_bundle.py            # dry run: lists what would change, pushes nothing
    python ingestion/push_data_bundle.py --push     # commit the changes and push them
    options: --remote URL_OR_PATH  --checkout DIR  --force  --max-shrink 0.10

Cloud routines build from that repo (docs/cloud_routines.md, "Raw data"); a stale one made a cloud run commit a venues.json
with 8,300 fewer venues (2026-11-15). For every CSV / WKT in the raw folder (ingestion/rawdir.py) it compares the file's
content hash with what the data repo holds (unpacked the way cloud_bootstrap.py does). Only changed files are re-gzipped
(make_data_bundle.bundle_file; anything over 80 MiB is split in `.gz.partNN` chunks, `overture_addresses` included),
copied into the checkout's `raw/`, committed and pushed. Never pushes without --push.
Refuses (exit 1) when a file is more than --max-shrink (10%) smaller than the data repo's copy, unless --force: a truncated
extract must not replace a good one. Files only the data repo has are left alone.
The checkout lives OUTSIDE this repo: --checkout, else $COURTCONNECT_DATA_REPO, else a sibling `courtconnect-data` folder
next to the main checkout (shallow clone made on first use). Needs git credentials for the remote (`gh auth setup-git`).
Never reads .env.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

from make_data_bundle import bundle_file
from rawdir import ROOT, raw_dir

REMOTE = "https://github.com/abov/courtconnect-data.git"
CHUNK = 80 * 1024 * 1024  # same size as the existing `split -b 80M` parts (GitHub refuses files over 100 MB)


def git(cwd: Path, *args: str, capture: bool = False) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, check=True, text=True, capture_output=capture)
    return r.stdout.strip() if capture else ""


def main_checkout() -> Path:
    """The main checkout of this repo (raw_dir() is <main>/data/raw unless $COURTCONNECT_DATA_DIR moves it)."""
    out = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    common = (ROOT / out).resolve() if out else ROOT / ".git"
    return common.parent if common.name == ".git" else ROOT


def checkout_dir(arg: str | None) -> Path:
    main = main_checkout().resolve()
    path = Path(arg or os.environ.get("COURTCONNECT_DATA_REPO") or main.parent / "courtconnect-data").resolve()
    for repo in {ROOT.resolve(), main}:
        if path == repo or repo in path.parents:
            sys.exit(f"refusing: the data-repo checkout {path} is inside {repo}; pass --checkout outside this repo")
    return path


def ensure_checkout(path: Path, remote: str) -> Path:
    """Clone (shallow) or fast-forward the checkout; returns its raw/ folder."""
    if not (path / ".git").exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        print(f"cloning {remote} -> {path}")
        subprocess.run(["git", "clone", "-q", "--depth", "1", remote, str(path)], check=True)
    else:
        if git(path, "status", "--porcelain", capture=True):
            sys.exit(f"{path} has uncommitted changes; clean it or pass another --checkout")
        branch = git(path, "rev-parse", "--abbrev-ref", "HEAD", capture=True)
        git(path, "fetch", "-q", "--depth", "1", "origin", branch)
        git(path, "reset", "-q", "--hard", f"origin/{branch}")
    return path / "raw"


class Joined:
    """Read-only file object over several files in order (the .partNN chunks are slices of ONE gzip stream)."""

    def __init__(self, parts: list[Path]):
        self.it, self.cur = iter(parts), None

    def read(self, n: int = -1) -> bytes:
        while True:
            if self.cur is None:
                p = next(self.it, None)
                if p is None:
                    return b""
                self.cur = open(p, "rb")
            data = self.cur.read(n)
            if data:
                return data
            self.cur.close()
            self.cur = None


def repo_copy(raw: Path, name: str) -> tuple[str, int] | None:
    """(sha256, size) of the unpacked content the data repo holds for `name`, or None."""
    parts = sorted(raw.glob(name + ".gz*"))
    if not parts:
        return None
    h, size = hashlib.sha256(), 0
    with gzip.GzipFile(fileobj=Joined(parts)) as z:
        while chunk := z.read(1 << 20):
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size


def local_copy(src: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    with open(src, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest(), src.stat().st_size


def plan(raw: Path, local: Path, max_shrink: float) -> list[dict]:
    rows = []
    for src in sorted(local.iterdir()):
        if not src.is_file() or src.suffix not in (".csv", ".wkt"):
            continue
        new_hash, new_size = local_copy(src)
        old = repo_copy(raw, src.name)
        row = {"src": src, "new": new_size, "old": old[1] if old else None, "status": "new"}
        if old:
            row["status"] = "unchanged" if old[0] == new_hash else "changed"
            if row["status"] == "changed" and old[1] and new_size < old[1] * (1 - max_shrink):
                row["status"] = "SHRANK"
        rows.append(row)
    return rows


def report(rows: list[dict], raw: Path) -> None:
    print(f"{'file':34} {'local MB':>9} {'repo MB':>9}  status")
    for r in rows:
        old = f"{r['old'] / 1e6:9.1f}" if r["old"] is not None else f"{'-':>9}"
        extra = f" ({(1 - r['new'] / r['old']) * 100:.0f}% smaller)" if r["status"] == "SHRANK" else ""
        print(f"{r['src'].name:34} {r['new'] / 1e6:9.1f} {old}  {r['status']}{extra}")
    here = {r["src"].name for r in rows}
    for name in sorted({p.name.split(".gz")[0] for p in raw.glob("*.gz*")} - here):
        print(f"{name:34} {'-':>9} {'':>9}  only in the data repo (left alone)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--push", action="store_true", help="commit and push (default: dry run)")
    ap.add_argument("--force", action="store_true", help="allow a file to shrink more than --max-shrink")
    ap.add_argument("--max-shrink", type=float, default=0.10)
    ap.add_argument("--remote", default=REMOTE, help="git URL or path of the data repo (tests pass a local bare repo)")
    ap.add_argument("--checkout", help="where the data repo is checked out (outside this repo)")
    a = ap.parse_args()

    local = raw_dir()
    if not local.is_dir():
        sys.exit(f"{local} not found: run the extract + load first")
    path = checkout_dir(a.checkout)
    raw = ensure_checkout(path, a.remote)
    raw.mkdir(exist_ok=True)

    print(f"local raw: {local}\ndata repo: {path}")
    rows = plan(raw, local, a.max_shrink)
    report(rows, raw)
    todo = [r for r in rows if r["status"] != "unchanged"]
    shrank = [r["src"].name for r in rows if r["status"] == "SHRANK"]
    if shrank and not a.force:
        sys.exit(f"\nrefusing: {', '.join(shrank)} shrank more than {a.max_shrink:.0%} vs the data repo (truncated extract?). "
                 "Check the extract; --force only if the drop is real.")
    if not todo:
        print("\ndata repo is up to date; nothing to push.")
        return
    if not a.push:
        print(f"\ndry run: {len(todo)} file(s) would be committed and pushed. Re-run with --push (make push-data ARGS=--push).")
        return

    with tempfile.TemporaryDirectory() as tmp:
        for r in todo:
            name = r["src"].name
            made = bundle_file(r["src"], Path(tmp), CHUNK)
            for stale in raw.glob(name + ".gz*"):  # drop old parts when the part count changes
                stale.unlink()
            for f in made:
                shutil.copy2(f, raw / f.name)
                f.unlink()
    git(path, "add", "-A", "raw")
    if not git(path, "status", "--porcelain", capture=True):
        print("nothing to commit.")
        return
    msg = f"Raw data refresh {date.today():%Y-%m-%d}: " + ", ".join(r["src"].name for r in todo)
    git(path, "commit", "-q", "-m", msg[:200])
    branch = git(path, "rev-parse", "--abbrev-ref", "HEAD", capture=True)
    git(path, "push", "-q", "origin", f"HEAD:{branch}")
    print(f"\npushed {len(todo)} file(s) to {a.remote} ({branch}): {git(path, 'rev-parse', '--short', 'HEAD', capture=True)}")


if __name__ == "__main__":
    main()
