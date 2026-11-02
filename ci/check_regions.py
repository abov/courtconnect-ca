"""Offline check of the border clip in ingestion/overpass.py (uses the cached border WKT files) and that the dbt `regions` var matches regions.json.

Run: python ci/check_regions.py   (fetches a border from Overpass only if its cache file is missing)
     python ci/check_regions.py --config-only   (offline, no shapely: only the dbt var / fips checks; this one runs in CI)
"""
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ingestion"))
import overpass  # noqa: E402

# (lat, lon, expected region)
POINTS = [
    (38.9560, -119.9440, "CA"),   # South Lake Tahoe, CA side of Stateline
    (38.9680, -119.9420, "NV"),   # Stateline NV casino corridor
    (38.9500, -120.0300, "CA"),   # Lake Tahoe west shore, deep CA side
    (34.05, -118.25, "CA"),       # Los Angeles
    (36.17, -115.14, "NV"),       # Las Vegas
    (39.53, -119.81, "NV"),       # Reno
    (45.52, -122.68, "OR"),       # Portland
    (44.05, -123.09, "OR"),       # Eugene
    (44.06, -121.31, "OR"),       # Bend
    (42.19, -122.71, "OR"),       # Ashland, just north of the California line
    (41.73, -122.63, "CA"),       # Yreka, just south of it
    (42.22, -121.78, "OR"),       # Klamath Falls
    (44.03, -116.96, "OR"),       # Ontario, on the Idaho line
    (43.60, -116.20, None),       # Boise, Idaho
    (45.64, -122.66, None),       # Vancouver, Washington (None until Washington is added)
    (32.40, -117.00, None),       # Tijuana area, Mexico
]


def check_dbt_var() -> int:
    """The dbt macros read the regions var in transform/dbt_project.yml; it must equal the boxes in regions.json (ADR 0028)."""
    var = yaml.safe_load((Path(__file__).resolve().parent.parent / "transform" / "dbt_project.yml").read_text(encoding="utf-8"))["vars"]["regions"]
    want = {code: dict(zip(("south", "west", "north", "east"), cfg["bbox"])) for code, cfg in overpass.REGIONS.items()}
    ok = var == want and list(var) == list(want)
    print(f"{'ok  ' if ok else 'FAIL'} dbt_project.yml vars.regions matches ingestion/regions.json")
    if not ok:
        print(f"  dbt: {var}\n  json: {want}")
    fips = [c["fips"] for c in overpass.REGIONS.values() if c["fips"]]   # blank = outside the US
    ok2 = all(len(f) == 2 and f.isdigit() for f in fips) and len(set(fips)) == len(fips)
    print(f"{'ok  ' if ok2 else 'FAIL'} Census fips codes are unique two-digit strings {fips}")
    return (not ok) + (not ok2)


def check_outlines() -> int:
    """Every state in regions.json needs its state line in app/data/calneva_outline.json (drawn under the pins). A new state fails CI
    until `python ingestion/add_state_outline.py` has added it."""
    fc = json.loads((Path(__file__).resolve().parent.parent / "app" / "data" / "calneva_outline.json").read_text(encoding="utf-8"))
    have = {f["properties"]["name"] for f in fc["features"]}
    code_to_name = {c: n.title() for n, c in overpass.STATE_AREAS.items()}
    missing = [code_to_name[c] for c in overpass.REGIONS if code_to_name[c] not in have]
    print(f"{'ok  ' if not missing else 'FAIL'} calneva_outline.json has a state line for every region in regions.json")
    if missing:
        print(f"  missing: {missing}; run python ingestion/add_state_outline.py (needs the cached data/raw/*_border.wkt) and commit app/data/calneva_outline.json")
    return bool(missing)


def main() -> int:
    bad = check_dbt_var() + check_outlines()
    if "--config-only" in sys.argv:
        return 1 if bad else 0
    for lat, lon, want in POINTS:
        got = overpass.region_at(lat, lon)
        ok = got == want
        bad += not ok
        print(f"{'ok  ' if ok else 'FAIL'} ({lat}, {lon}) want {want} got {got}")
    for area, pts in {"tahoe": [(38.9560, -119.9440), (38.9680, -119.9420)], "lv": [(36.17, -115.14)]}.items():
        for lat, lon in pts:
            ok = overpass.keep(lat, lon, area)
            bad += not ok
            print(f"{'ok  ' if ok else 'FAIL'} keep {area} ({lat}, {lon})")
    ok = not overpass.keep(36.17, -115.14, "california")
    bad += not ok
    print(f"{'ok  ' if ok else 'FAIL'} Las Vegas not kept for --area california")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
