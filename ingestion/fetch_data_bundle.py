"""Download the public raw-data bundle (a GitHub Release) into the raw folder, so nobody has to re-run the 15-20 min extract.

    python ingestion/fetch_data_bundle.py [--repo OWNER/NAME] [--tag TAG] [--build]

Default: the latest release of abov/courtconnect-ca (a fork passes --repo). Assets are the gzipped CSVs made by
`python ingestion/make_data_bundle.py` (big files split in `.partNN` chunks, same layout as cloud_bootstrap.py unpacks).
Public release: no token needed. Unpacks into the default raw folder (ingestion/rawdir.py); --build then runs fresh_db.py.
The bundle is a snapshot of OSM + Overture extracts (ODbL / Overture licences, see NOTICE.md); it is never committed to git.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from cloud_bootstrap import unpack
from rawdir import ROOT, raw_dir
from useragent import HEADERS


def get(url: str, dest: Path | None = None):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=120) as r:
        if dest is None:
            return json.load(r)
        with open(dest, "wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="abov/courtconnect-ca")
    ap.add_argument("--tag", default="latest")
    ap.add_argument("--build", action="store_true", help="run ingestion/fresh_db.py afterwards")
    a = ap.parse_args()

    path = "latest" if a.tag == "latest" else f"tags/{a.tag}"
    rel = get(f"https://api.github.com/repos/{a.repo}/releases/{path}")
    assets = [x for x in rel["assets"] if ".gz" in x["name"]]
    if not assets:
        sys.exit(f"release {rel.get('tag_name')} of {a.repo} has no .gz assets")
    print(f"release {rel['tag_name']}: {len(assets)} files")
    with tempfile.TemporaryDirectory() as tmp:
        for x in assets:
            print(f"  downloading {x['name']} ({x['size'] / 1e6:.1f} MB)")
            get(x["browser_download_url"], Path(tmp) / x["name"])
        dest = raw_dir()
        print(f"unpacking -> {dest}")
        unpack(Path(tmp), dest)
    if a.build:
        subprocess.run([sys.executable, str(ROOT / "ingestion" / "fresh_db.py")], cwd=ROOT, check=True)
    else:
        print("next: make fresh-db")


if __name__ == "__main__":
    main()
