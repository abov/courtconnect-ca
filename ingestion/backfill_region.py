"""One-off: add the `region` column (CA / NV, from the border polygon) to raw CSVs written before ADR 0014 step 2.

    python ingestion/backfill_region.py                          (rewrites data/raw/*.csv in place; safe to re-run)
    python ingestion/backfill_region.py --data-dir ci/fixtures   (the CI sample)

New extracts write `region` themselves. Overture's own address state column `region` is renamed `address_region` first.
Uses the cached border files (data/raw/*_border.wkt); a missing cache is fetched once from Overpass.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import overpass  # noqa: E402
from rawdir import raw_path

FILES = {"osm_courts.csv": ("lat", "lon"), "osm_walls.csv": ("lat", "lon"), "overture_places.csv": ("lat", "lon"),
         "osm_parents.csv": None}   # parents: centre of the bounding box


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=raw_path(""))
    raw = Path(ap.parse_args().data_dir)
    for name, cols in FILES.items():
        path = raw / name
        if not path.exists():
            print(f"skip {name} (not found)")
            continue
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
        if name == "overture_places.csv" and "address_region" not in df.columns:
            df = df.rename(columns={"region": "address_region"})
        if cols:
            lat, lon = pd.to_numeric(df[cols[0]]), pd.to_numeric(df[cols[1]])
        else:
            lat = (pd.to_numeric(df["minlat"]) + pd.to_numeric(df["maxlat"])) / 2
            lon = (pd.to_numeric(df["minlon"]) + pd.to_numeric(df["maxlon"])) / 2
        df["region"] = [overpass.region_at(a, b) or "" for a, b in zip(lat, lon)]
        df.to_csv(path, index=False)
        print(f"{name}: {df['region'].value_counts(dropna=False).to_dict()}")


if __name__ == "__main__":
    main()
