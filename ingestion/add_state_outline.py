"""Add the state lines of every covered state that is missing from app/data/state_outline.json (drawn under the pins on the map).

    python ingestion/add_state_outline.py

California and Nevada were drawn by hand in 2026-10. A state added later is taken from its OSM border polygon (the cached
data/raw/<code>_border.wkt that the extract clip uses), simplified to about 0.01 degrees (1 km) and rounded to 2 decimals, so
the file stays small. Existing features are left alone. Run it after adding a state to ingestion/regions.json.
"""
from __future__ import annotations

import json
from pathlib import Path

from shapely import wkt
from shapely.geometry import mapping

from overpass import REGIONS, STATE_AREAS

OUT = Path(__file__).resolve().parent.parent / "app" / "data" / "state_outline.json"


def ring(coords) -> list:
    return [[round(x, 2), round(y, 2)] for x, y in coords]


def main() -> None:
    fc = json.loads(OUT.read_text(encoding="utf-8"))
    have = {f["properties"]["name"] for f in fc["features"]}
    for code, cfg in REGIONS.items():
        name = {c: n for n, c in STATE_AREAS.items()}[code].replace("_", " ").title()
        if name in have:
            continue
        poly = wkt.loads(Path(cfg["cache"]).read_text(encoding="utf-8")).simplify(0.01, preserve_topology=True)
        geom = mapping(poly)
        coords = [[ring(r) for r in geom["coordinates"]]] if geom["type"] == "Polygon" else [[ring(r) for r in p] for p in geom["coordinates"]]
        fc["features"].append({"type": "Feature", "properties": {"name": name}, "geometry": {"type": geom["type"], "coordinates": coords[0] if geom["type"] == "Polygon" else coords}})
        print(f"added {name} ({code})")
    OUT.write_text(json.dumps(fc, separators=(",", ":")), encoding="utf-8")
    print(f"{len(fc['features'])} features -> {OUT} ({OUT.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
