"""Build app/data/mx_state_outline.json: one light line per Mexican federal entity (31 states + Mexico City), ADR 0034.

    python ingestion/build_mx_state_outline.py                  # newest Overture release
    python ingestion/build_mx_state_outline.py --release 2026-10-21.0

Source: Overture divisions `division_area`, subtype `region`, class `land` (CDLA-Permissive, same bucket as the municipio
extract). Simplified to about 0.03 degrees (3 km), islands under about 200 km2 dropped, rounded to 2 decimals. Each feature has
`name` and `code` (ISO 3166-2, e.g. MX-BCN), the key planned for the `subregion` column. The map draws them under the pins
in a lighter style than the covered-state lines; the file is separate so the five US states' outline file is untouched.
Needs DuckDB's spatial extension and network access (range reads of the public bucket; no API key).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import duckdb
from shapely import wkt
from shapely.geometry import MultiPolygon, mapping

from extract_overture_places import BUCKET, latest_release

OUT = Path(__file__).resolve().parent.parent / "app" / "data" / "mx_state_outline.json"
SIMPLIFY_DEG = 0.03   # about 3 km: the line is light and drawn under the pins
MIN_AREA_DEG2 = 0.02  # about 200 km2


def rnd(c):
    return [round(c[0], 2), round(c[1], 2)] if isinstance(c[0], (int, float)) else [rnd(x) for x in c]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--release", default=None)
    args = ap.parse_args()
    release = args.release or latest_release()
    con = duckdb.connect()
    con.execute("install httpfs; load httpfs; set s3_region='us-west-2';")
    try:
        con.execute("load spatial")
    except duckdb.Error:
        con.execute("install spatial")
        con.execute("load spatial")
    path = f"s3://{BUCKET}/release/{release}/theme=divisions/type=division_area/*"
    rows = con.execute(f"""
        select region, names.primary, st_astext(geometry)
        from read_parquet('{path}', hive_partitioning=1)
        where country = 'MX' and subtype = 'region' and class = 'land' and region is not null
        order by region""").fetchall()
    feats = []
    for code, name, w in rows:
        g = wkt.loads(w)
        if g.geom_type == "MultiPolygon":   # drop specks (small islands): a light line does not need them
            keep = [p for p in g.geoms if p.area >= MIN_AREA_DEG2]
            g = MultiPolygon(keep or [max(g.geoms, key=lambda p: p.area)])
        geom = mapping(g.simplify(SIMPLIFY_DEG, preserve_topology=True))
        feats.append({"type": "Feature", "properties": {"name": name, "code": code},
                      "geometry": {"type": geom["type"], "coordinates": rnd(geom["coordinates"])}})
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Overture {release}: {len(feats)} entities -> {OUT} ({OUT.stat().st_size / 1024:.1f} KB)")
    if len(feats) != 32:
        print(f"WARNING: expected 32 federal entities, got {len(feats)}: {[f['properties']['code'] for f in feats]}")


if __name__ == "__main__":
    main()
