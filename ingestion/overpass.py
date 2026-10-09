"""Shared helpers for talking to the Overpass API (OpenStreetMap)."""
from __future__ import annotations

import sys
import time

import requests

URLS = [  # ordered by observed reliability; the first healthy one wins
    "https://overpass.openstreetmap.fr/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
]

# south, west, north, east
BBOXES = {
    "la": (33.70, -118.67, 34.34, -118.15),
    "sf": (37.60, -122.55, 37.90, -122.30),
    "sd": (32.55, -117.30, 33.05, -116.95),
}


def california_tiles(lat_step: float = 1.6, lon_step: float = 2.1):
    """Cover California's bounding box with tiles small enough for the free Overpass servers.
    Every query is also clipped to the real state polygon, so Nevada/Oregon/Mexico never leak in."""
    s0, n0, w0, e0 = 32.5, 42.1, -124.5, -114.0
    tiles, lat = [], s0
    while lat < n0:
        lon = w0
        while lon < e0 - 0.01:
            tiles.append((round(lat, 3), round(lon, 3),
                          round(min(lat + lat_step, n0), 3), round(min(lon + lon_step, e0), 3)))
            lon += lon_step
        lat += lat_step
    return tiles


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
    elements for them. We fetch by bbox and clip to the real state border locally (california_border)."""
    s, w, n, e = bbox
    return f"[out:json][timeout:{timeout}][bbox:{s},{w},{n},{e}];"


_BORDER = None


def california_border(cache: str = "data/raw/ca_border.wkt"):
    """California's border as a shapely (prepared) polygon, built from OSM relation 165475 and cached on disk."""
    global _BORDER
    if _BORDER is not None:
        return _BORDER
    from pathlib import Path

    from shapely import wkt
    from shapely.geometry import LineString
    from shapely.ops import polygonize, unary_union
    from shapely.prepared import prep

    path = Path(cache)
    if path.exists():
        poly = wkt.loads(path.read_text(encoding="utf-8"))
    else:
        rel = run("[out:json][timeout:120];rel(165475);out geom;", "california border")[0]
        lines = [LineString([(p["lon"], p["lat"]) for p in m["geometry"]])
                 for m in rel["members"] if m["type"] == "way" and m.get("role") == "outer" and m.get("geometry")]
        poly = unary_union(list(polygonize(unary_union(lines))))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(poly.wkt, encoding="utf-8")
    _BORDER = prep(poly)
    return _BORDER


def in_california(lat, lon) -> bool:
    from shapely.geometry import Point
    return lat is not None and lon is not None and california_border().contains(Point(lon, lat))
