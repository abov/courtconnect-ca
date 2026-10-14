"""Offline check of the CA/NV border clip in ingestion/overpass.py (uses the cached border WKT files).

Run: python ci/check_regions.py   (fetches a border from Overpass only if its cache file is missing)
"""
import sys
from pathlib import Path

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
    (45.52, -122.68, None),       # Portland, Oregon
    (32.40, -117.00, None),       # Tijuana area, Mexico
]


def main() -> int:
    bad = 0
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
