"""Scaling benchmark: how do build time, memory and the map payload grow as the raw data grows?

    python ingestion/bench_scale.py 1 3 10            # scales to try (multiples of today's CA + NV raw data)
    python ingestion/bench_scale.py 10 --keep         # keep the scratch database afterwards

For each scale it copies courtconnect.duckdb to a scratch folder, replicates the OSM and Overture raw tables N times
(replica k is shifted on a lat/lon grid so replicas never overlap, ids get a per-replica offset), runs `dbt run` against
the copy and records the wall time, the slowest models, the peak memory of the dbt process and the size of the venue
export. Nothing in the real database or in app/ is touched. Seeds and manual CSVs stay at 1x (they are hand-curated
and do not grow with area), and tests are skipped (the region bounding-box tests would reject shifted points): this
measures the transform, not correctness. Results go to stdout as markdown for docs/scale.md.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
SRC_DB = ROOT / "courtconnect.duckdb"
# table -> (id column, id kind, [(lat col, lon col), ...])
REPLICATE = {
    "osm_courts": ("osm_id", "int", [("lat", "lon")]),
    "osm_parents": ("osm_id", "int", [("minlat", "minlon"), ("maxlat", "maxlon")]),
    "osm_walls": ("osm_id", "int", [("lat", "lon")]),
    "overture_places": ("place_id", "str", [("lat", "lon")]),
    "overture_addresses": ("address_id", "str", [("lat", "lon")]),
}


def replicate(db: Path, scale: int) -> dict[str, int]:
    """Grow each raw table to `scale` copies in place; return row counts."""
    con = duckdb.connect(str(db))
    counts = {}
    for table, (idc, kind, coords) in REPLICATE.items():
        base = con.execute(f"select count(*) from raw.{table}").fetchone()[0]
        cols = [r[0] for r in con.execute(f"describe raw.{table}").fetchall()]
        for k in range(1, scale):
            dlon, dlat = (k % 10) * 11.0, -(k // 10) * 10.0
            sel = []
            for c in cols:
                if c == idc:
                    sel.append(f"{c} + {k * 10**12}" if kind == "int" else f"{c} || '_r{k}'")
                elif any(c == la for la, _ in coords):
                    sel.append(f"{c} + ({dlat})")
                elif any(c == lo for _, lo in coords):
                    sel.append(f"{c} + ({dlon})")
                else:
                    sel.append(c)
            con.execute(f"insert into raw.{table} select {', '.join(sel)} from raw.{table} limit {base}")
        counts[table] = con.execute(f"select count(*) from raw.{table}").fetchone()[0]
    con.close()
    return counts


def run_dbt(work: Path, db: Path) -> tuple[float, list[tuple[str, float]], float]:
    """dbt run against the scratch db; returns (seconds, slowest models, peak working set in MB)."""
    prof = work / "profiles"
    prof.mkdir(exist_ok=True)
    (prof / "profiles.yml").write_text(
        f"courtconnect:\n  target: duckdb\n  outputs:\n    duckdb:\n      type: duckdb\n      path: {db.as_posix()}\n      threads: 4\n")
    exe = Path(sys.executable).parent / ("dbt.exe" if sys.platform == "win32" else "dbt")
    cmd = [str(exe), "run", "--project-dir", "transform", "--profiles-dir", str(prof), "--target-path", str(work / "target")]
    t0 = time.perf_counter()
    proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    peak = 0.0
    try:
        import psutil
        p = psutil.Process(proc.pid)
        while proc.poll() is None:
            try:
                rss = p.memory_info().rss + sum(c.memory_info().rss for c in p.children(recursive=True))
                peak = max(peak, rss / 1e6)
            except psutil.Error:
                pass
            time.sleep(0.5)
    except ImportError:
        proc.wait()
        peak = float("nan")
    secs = time.perf_counter() - t0
    if proc.returncode:
        raise SystemExit(f"dbt run failed (exit {proc.returncode}); run it by hand against {db} to see why")
    results = json.loads((work / "target" / "run_results.json").read_text())["results"]
    slow = sorted(((r["unique_id"].split(".")[-1], r["execution_time"]) for r in results), key=lambda x: -x[1])[:5]
    return secs, slow, peak


def export_size(db: Path) -> tuple[int, float]:
    """Venue count and the approximate JSON size the map would load (compact rows, same shape as the real export)."""
    con = duckdb.connect(str(db), read_only=True)
    n = con.execute("select count(*) from marts.mart_venue_finder").fetchone()[0]
    rows = con.execute("select * from marts.mart_venue_finder").fetchall()
    con.close()
    return n, len(json.dumps(rows, default=str, separators=(",", ":"))) / 1e6


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("scales", nargs="+", type=int)
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args()
    print("| scale | raw rows (addresses) | dbt run | peak memory | venues | venue payload | slowest models |")
    print("|---|---|---|---|---|---|---|")
    for scale in args.scales:
        work = Path(tempfile.mkdtemp(prefix=f"bench{scale}x_"))
        db = work / "bench.duckdb"
        shutil.copy(SRC_DB, db)
        counts = replicate(db, scale)
        secs, slow, peak = run_dbt(work, db)
        n, mb = export_size(db)
        slow_s = ", ".join(f"{m} {t:.0f}s" for m, t in slow[:3])
        print(f"| {scale}x | {counts['overture_addresses']:,} | {secs / 60:.1f} min | {peak / 1000:.1f} GB | {n:,} | {mb:.1f} MB | {slow_s} |", flush=True)
        if not args.keep:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
