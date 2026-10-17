"""Shared helpers for talking to the Overpass API (OpenStreetMap)."""
from __future__ import annotations

import sys
import time

import requests
from rawdir import raw_path

URLS = [  # ordered by observed reliability; the first healthy one wins
    "https://overpass.openstreetmap.fr/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
]

# Regions we cover. bbox = south, west, north, east. The border relation is the real filter; the bbox only
# bounds the tiles. Nevada relation 165473 checked on OSM (name=Nevada, admin_level=4, ISO3166-2=US-NV).
REGIONS = {
    "CA": {"bbox": (32.5, -124.5, 42.1, -114.0), "relation": 165475, "cache": raw_path("ca_border.wkt")},
    "NV": {"bbox": (35.0, -120.01, 42.0, -114.03), "relation": 165473, "cache": raw_path("nv_border.wkt")},
}

# south, west, north, east
BBOXES = {
    "la": (33.70, -118.67, 34.34, -118.15),
    "sf": (37.60, -122.55, 37.90, -122.30),
    "sd": (32.55, -117.30, 33.05, -116.95),
    "lv": (35.95, -115.40, 36.35, -114.85),      # Las Vegas / Henderson
    "reno": (39.40, -119.95, 39.70, -119.65),    # Reno / Sparks
    "carson": (39.10, -119.85, 39.25, -119.70),  # Carson City
    "tahoe": (38.85, -120.20, 39.35, -119.85),   # Lake Tahoe, straddles the CA/NV line
}

# Which state(s) a named area may keep rows from (the polygon clip decides, per point).
AREA_REGIONS = {"california": ("CA",), "nevada": ("NV",), "la": ("CA",), "sf": ("CA",), "sd": ("CA",),
                "lv": ("NV",), "reno": ("NV",), "carson": ("NV",), "tahoe": ("CA", "NV")}


def tiles(region: str, lat_step: float = 1.6, lon_step: float = 2.1):
    """Cover a region's bounding box with tiles small enough for the free Overpass servers.
    Every query is also clipped to the real state polygon (in_region), so neighbours never leak in."""
    s0, w0, n0, e0 = REGIONS[region]["bbox"]
    out, lat = [], s0
    while lat < n0:
        lon = w0
        while lon < e0 - 0.01:
            out.append((round(lat, 3), round(lon, 3),
                        round(min(lat + lat_step, n0), 3), round(min(lon + lon_step, e0), 3)))
            lon += lon_step
        lat += lat_step
    return out


def area_tiles(area: str):
    """Tiles for an --area value: a state name (california/nevada) or a BBOXES metro key."""
    return tiles(AREA_REGIONS[area][0]) if area in ("california", "nevada") else [BBOXES[area]]


def keep(lat, lon, area: str) -> bool:
    """True if the point lies inside one of the states allowed for this --area."""
    return region_at(lat, lon) in AREA_REGIONS[area]


def run(query: str, label: str = "", attempts: int = 4) -> list[dict]:
    last: Exception | None = None
    for url in URLS:
        for attempt in range(attempts):
            try:
                r = requests.post(url, data={"data": query}, timeout=330,
                                  headers={"User-Agent": "courtconnect-ca/0.1 (portfolio project)"})
                r.raise_for_status()
                return r.json()["elements"]
            except Exception as err:  # noqa: BLE001 - retry on any transport/parse error
                last = err
                wait = 8 * (attempt + 1)
                print(f"  {label} {url.split('/')[2]} attempt {attempt + 1} failed ({err}); retry in {wait}s",
                      file=sys.stderr, flush=True)
                time.sleep(wait)
    raise RuntimeError(f"All Overpass endpoints failed for {label}: {last}")


def _quadrants(b):
    s, w, n, e = b
    ms, mw = round((s + n) / 2, 4), round((w + e) / 2, 4)
    return [(s, w, ms, mw), (s, mw, ms, e), (ms, w, n, mw), (ms, mw, n, e)]


def fetch_adaptive(build_query, bbox, label: str, failed: list, depth: int = 0, max_depth: int = 3) -> list[dict]:
    """Run build_query(bbox). If the public servers time out, retry as four smaller tiles (recursively).
    Tiles that still fail at the smallest size are appended to `failed` so the caller can report them."""
    try:
        return run(build_query(bbox), label, attempts=1)
    except RuntimeError:
        if depth >= max_depth:
            failed.append(bbox)
            print(f"  GIVING UP on {bbox} after splitting {depth}x", file=sys.stderr, flush=True)
            return []
        print(f"  {label}: splitting {bbox} into 4", file=sys.stderr, flush=True)
        out: list[dict] = []
        for i, q in enumerate(_quadrants(bbox), 1):
            out += fetch_adaptive(build_query, q, f"{label}.{i}", failed, depth + 1, max_depth)
            time.sleep(1)
        return out


def header(bbox: tuple[float, float, float, float], timeout: int = 300) -> str:
    """Overpass settings line restricting the whole query to a bounding box (south, west, north, east).
    NOTE: we deliberately do NOT use Overpass `area` filters. Some public mirrors silently return zero
    elements for them. We fetch by bbox and clip to the real state border locally (in_region)."""
    s, w, n, e = bbox
    return f"[out:json][timeout:{timeout}][bbox:{s},{w},{n},{e}];"


_BORDERS: dict = {}


def border(region: str):
    """A region's border as a shapely (prepared) polygon, built from its OSM relation and cached on disk."""
    if region in _BORDERS:
        return _BORDERS[region]
    from pathlib import Path

    from shapely import wkt
    from shapely.geometry import LineString
    from shapely.ops import polygonize, unary_union
    from shapely.prepared import prep

    cfg = REGIONS[region]
    path = Path(cfg["cache"])
    if path.exists():
        poly = wkt.loads(path.read_text(encoding="utf-8"))
    else:
        rel = run(f"[out:json][timeout:120];rel({cfg['relation']});out geom;", f"{region} border")[0]
        lines = [LineString([(p["lon"], p["lat"]) for p in m["geometry"]])
                 for m in rel["members"] if m["type"] == "way" and m.get("role") == "outer" and m.get("geometry")]
        poly = unary_union(list(polygonize(unary_union(lines))))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(poly.wkt, encoding="utf-8")
    _BORDERS[region] = prep(poly)
    return _BORDERS[region]


def in_region(lat, lon, region: str) -> bool:
    from shapely.geometry import Point
    return lat is not None and lon is not None and border(region).contains(Point(lon, lat))


def region_at(lat, lon):
    """'CA', 'NV' or None (neither). Cheap bbox pre-check, then the polygon."""
    if lat is None or lon is None:
        return None
    for code, cfg in REGIONS.items():
        s, w, n, e = cfg["bbox"]
        if s <= lat <= n and w <= lon <= e and in_region(lat, lon, code):
            return code
    return None
