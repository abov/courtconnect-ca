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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "dist" / "data-bundle"))
    ap.add_argument("--max-mb", type=int, default=1500)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for src in sorted(raw_dir().iterdir()):
        if src.suffix not in (".csv", ".wkt") or src.name in SKIP:
            continue
        gz = out / (src.name + ".gz")
        with open(src, "rb") as fin, gzip.open(gz, "wb", compresslevel=6) as fout:
            shutil.copyfileobj(fin, fout)
        size = gz.stat().st_size
        if size > a.max_mb * 1_000_000:
            n = 0
            with open(gz, "rb") as f:
                while chunk := f.read(a.max_mb * 1_000_000):
                    (out / f"{gz.name}.part{n:02d}").write_bytes(chunk)
                    n += 1
            gz.unlink()
            print(f"{src.name}: {size / 1e6:.0f} MB -> {n} parts")
        else:
            print(f"{src.name}: {size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
