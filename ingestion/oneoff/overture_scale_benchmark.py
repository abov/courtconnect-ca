"""Measure how much of the Overture release the CA+NV extracts actually read (docs/planet_scale_plan.md).

For each theme (places, addresses; --themes adds e.g. buildings for release size and row count only):
  release size  sum of object sizes under the theme prefix (public S3 listing, no account)
  planet rows   count(*) over every file (answered from parquet footers)
  extract rows  rows the real extract query returns (same SQL as extract_overture_places / _addresses: keep in sync)
  bytes read    HTTP bytes DuckDB fetched for each step (DuckDB HTTP logging, sum of GET Content-Length)
  seconds       wall clock per step

    python ingestion/oneoff/overture_scale_benchmark.py                      # newest release
    python ingestion/oneoff/overture_scale_benchmark.py --release 2026-10-21.0 --themes places,addresses,buildings

Prints a result block and writes JSON next to the doc (docs/planet_scale_benchmark.json). Reads only; writes nothing to data/raw.
Overture keeps a release about 60 days, so a re-run on an old release id can fail.
"""
from __future__ import annotations

import argparse
import json
import platform
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # shared helpers in ingestion/
from extract_overture_places import BUCKET, latest_release
from rawdir import raw_path
from useragent import HEADERS as UA

THEMES = {"places": "type=place", "addresses": "type=address", "buildings": "type=building"}
CELLS_PER_DEGREE = 250   # same as extract_overture_addresses.py
BBOX = "bbox.xmin between -124.5 and -114.0 and bbox.ymin between 32.5 and 42.1"   # CA+NV box, same as both extracts


def release_size(release: str, theme: str) -> tuple[int, int]:
    """(files, bytes) under the theme prefix, via S3 ListObjectsV2 (1000 keys a page)."""
    prefix = f"release/{release}/theme={theme}/type={THEMES[theme].split('=')[1]}/"
    files = total = 0
    token = None
    while True:
        url = f"https://{BUCKET}.s3.amazonaws.com/?list-type=2&prefix={urllib.parse.quote(prefix)}"
        if token:
            url += "&continuation-token=" + urllib.parse.quote(token)
        xml = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read().decode()
        sizes = re.findall(r"<Size>(\d+)</Size>", xml)
        files += len(sizes)
        total += sum(int(s) for s in sizes)
        m = re.search(r"<NextContinuationToken>([^<]+)</NextContinuationToken>", xml)
        if not m:
            return files, total
        token = m.group(1)


def step(con: duckdb.DuckDBPyConnection, fn) -> dict:
    """Run fn(), return its value plus seconds and HTTP bytes/requests DuckDB made during it."""
    con.execute("CALL truncate_duckdb_logs()")
    t0 = time.time()
    value = fn()
    secs = time.time() - t0
    n, b = con.execute("""select count(*), coalesce(sum(try_cast(map_extract_value(response.headers, 'Content-Length') as bigint)), 0)
                          from duckdb_logs_parsed('HTTP') where request.type = 'GET'""").fetchone()
    return {"value": value, "seconds": round(secs, 1), "requests": n, "bytes": int(b)}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--release", default=None)
    ap.add_argument("--themes", default="places,addresses")
    ap.add_argument("--out", default="docs/planet_scale_benchmark.json")
    args = ap.parse_args()
    release = args.release or latest_release()
    themes = [t.strip() for t in args.themes.split(",")]
    print(f"Overture release {release}")

    con = duckdb.connect()
    con.execute("install httpfs; load httpfs; set s3_region='us-west-2'; set threads=8;")
    con.execute("CALL enable_logging('HTTP')")
    result = {"release": release, "run_on": time.strftime("%Y-%m-%d"), "duckdb": duckdb.__version__,
              "machine": f"{platform.system()} {platform.machine()}, {con.execute('select current_setting(\'threads\')').fetchone()[0]} threads",
              "themes": {}}

    for theme in themes:
        path = f"s3://{BUCKET}/release/{release}/theme={theme}/{THEMES[theme]}/*"
        files, size = release_size(release, theme)
        out = {"files": files, "release_bytes": size}
        rows = step(con, lambda: con.execute(f"select count(*) from read_parquet('{path}', hive_partitioning=1)").fetchone()[0])
        out["planet_rows"], out["count_step"] = rows.pop("value"), rows
        print(f"{theme}: {files} files, {size / 1e9:.1f} GB, {out['planet_rows']:,} rows (count read {rows['bytes'] / 1e6:.0f} MB)")

        if theme == "places":
            def extract():
                con.execute(f"""create or replace temp table places_out as
                    select id, names.primary, taxonomy.primary, taxonomy.hierarchy[1], taxonomy.hierarchy[2],
                           bbox.ymin, bbox.xmin, confidence, operating_status,
                           websites[1], phones[1],
                           addresses[1].freeform, addresses[1].locality, addresses[1].postcode, addresses[1].region,
                           sources[1].license, sources[1].dataset
                    from read_parquet('{path}', hive_partitioning=1)
                    where {BBOX}
                      and names.primary is not null
                      and (taxonomy.hierarchy[1] = 'sports_and_recreation'
                           or regexp_matches(coalesce(taxonomy.primary, ''),
                                'tennis|pickle|padel|squash|badminton|racquet|racket|recreation|athletic|country_club|community_center|sports'))""")
                return con.execute("select count(*) from places_out").fetchone()[0]
        elif theme == "addresses":
            def extract():
                con.execute(f"""create or replace temp table pins as
                    select lat, lon from read_csv_auto('{raw_path("osm_courts.csv")}') where lat is not null and lon is not null
                    union all select lat, lon from read_csv_auto('{raw_path("overture_places.csv")}') where lat is not null and lon is not null
                    union all select lat, lon from read_csv_auto('transform/seeds/manual_venues.csv') where lat is not null and lon is not null""")
                if Path(raw_path("osm_courts_nv.csv")).exists():
                    con.execute(f"insert into pins select lat, lon from read_csv_auto('{raw_path('osm_courts_nv.csv')}') where lat is not null and lon is not null")
                con.execute(f"""create or replace temp table cells as
                    select distinct cx + dx as cx, cy + dy as cy
                    from (select cast(floor(lon * {CELLS_PER_DEGREE}) as integer) as cx, cast(floor(lat * {CELLS_PER_DEGREE}) as integer) as cy from pins) c,
                         (select unnest([-1, 0, 1]) as dx), (select unnest([-1, 0, 1]) as dy)""")
                con.execute("CALL truncate_duckdb_logs()")   # pin/cell setup reads local files only; measure the S3 query alone
                con.execute(f"""create or replace temp table addr_out as
                    select a.id as address_id, a.number as house_number, a.street, a.unit, a.postcode,
                           coalesce(a.postal_city, a.address_levels[2].value) as city, a.address_levels[1].value as state,
                           a.bbox.ymin as lat, a.bbox.xmin as lon
                    from read_parquet('{path}', hive_partitioning=1) a
                    join cells c on c.cx = cast(floor(a.bbox.xmin * {CELLS_PER_DEGREE}) as integer)
                                and c.cy = cast(floor(a.bbox.ymin * {CELLS_PER_DEGREE}) as integer)
                    where a.{BBOX}
                      and a.country = 'US' and a.number is not null and a.street is not null""")
                return con.execute("select count(*) from addr_out").fetchone()[0]
        else:
            result["themes"][theme] = out   # size and row count only
            continue

        ex = step(con, extract)
        out["extract_rows"], out["extract_step"] = ex.pop("value"), ex
        out["pct_of_release_bytes"] = round(100 * ex["bytes"] / size, 2)
        result["themes"][theme] = out
        print(f"{theme}: extract kept {out['extract_rows']:,} rows, read {ex['bytes'] / 1e6:.0f} MB in {ex['requests']} requests, "
              f"{ex['seconds']} s = {out['pct_of_release_bytes']}% of the theme")

    Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
