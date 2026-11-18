"""Pack the raw CSVs into a release-ready bundle (owner step: upload the files to a GitHub Release).

    python ingestion/make_data_bundle.py [--out dist/data-bundle] [--max-mb 1500]

Gzips every CSV / WKT in the raw folder (ingestion/rawdir.py); files whose .gz is over --max-mb are split into
`.gz.partNN` byte chunks (GitHub allows 2 GB per release asset). Skips goatcounter_daily.csv (usage counts are not part
of the public data). Then publish, e.g.:  gh release create data-YYYY-MM-DD dist/data-bundle/* --notes "..."
Notes should say: OSM data (c) OpenStreetMap contributors, ODbL; Overture Maps data under its licences (NOTICE.md).
"""
from __future__ import annotations

import argparse
import gzip
import shutil
from pathlib import Path

from rawdir import ROOT, raw_dir

SKIP = {"goatcounter_daily.csv"}


def bundle_file(src: Path, out: Path, max_bytes: int) -> list[Path]:
    """Gzip one raw file into `out` (reproducible: no timestamp, so the same data gives the same bytes).

    A .gz over max_bytes is split into `.gz.partNN` byte slices of ONE gzip stream (cloud_bootstrap.unpack joins them).
    Returns the files written; push_data_bundle.py uses it too.
    """
    out.mkdir(parents=True, exist_ok=True)
    gz = out / (src.name + ".gz")
    with open(src, "rb") as fin, open(gz, "wb") as raw, gzip.GzipFile("", "wb", 6, raw, mtime=0) as fout:
        shutil.copyfileobj(fin, fout)
    if gz.stat().st_size <= max_bytes:
        return [gz]
    parts = []
    with open(gz, "rb") as f:
        while chunk := f.read(max_bytes):
            part = out / f"{gz.name}.part{len(parts):02d}"
            part.write_bytes(chunk)
            parts.append(part)
    gz.unlink()
    return parts


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "dist" / "data-bundle"))
    ap.add_argument("--max-mb", type=int, default=1500)
    a = ap.parse_args()
    out = Path(a.out)
    for src in sorted(raw_dir().iterdir()):
        if src.suffix not in (".csv", ".wkt") or src.name in SKIP:
            continue
        files = bundle_file(src, out, a.max_mb * 1_000_000)
        size = sum(f.stat().st_size for f in files)
        print(f"{src.name}: {size / 1e6:.0f} MB -> {len(files)} parts" if len(files) > 1 else f"{src.name}: {size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
