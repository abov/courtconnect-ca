"""Extract racket-sport-related places in California from the Overture Maps places dataset.

Overture publishes a global places dataset (businesses, clubs, venues) as GeoParquet on S3. Its places data is licensed
CDLA-Permissive-2.0 / Apache-2.0 / CC0, so unlike Google Places it may be stored and republished (with attribution; see NOTICE.md).

    python ingestion/extract_overture_places.py                    # newest release
    python ingestion/extract_overture_places.py --release 2026-09-23.1

Reads only what it needs straight from S3 (DuckDB range requests); nothing is downloaded wholesale.
Keeps a place if its Overture category is a racket sport OR its business name mentions a sport term (see
build_search_terms.py). Whether a name match counts as evidence is decided later, in dbt.

Output: data/raw/overture_places.csv
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import urllib.request
from pathlib import Path

import duckdb

import overpass  # reused for the California border clip

BUCKET = "overturemaps-us-west-2"
SEEDS = Path("transform/seeds")
FIELDS = ["place_id", "name", "category", "top_category", "sub_category", "lat", "lon", "confidence", "operating_status",
          "website", "phone", "address", "city", "postcode", "region", "license", "source_dataset", "release"]


def latest_release() -> str:
    url = f"https://{BUCKET}.s3.amazonaws.com/?list-type=2&prefix=release/&delimiter=/"
    xml = urllib.request.urlopen(url, timeout=60).read().decode()
    rel = sorted(set(re.findall(r"release/([0-9]{4}-[0-9]{2}-[0-9]{2}\.[0-9]+)/", xml)))
    if not rel:
        raise SystemExit("could not list Overture releases")
    return rel[-1]


def norm(s: str) -> str:
    """Same normalisation dbt uses for name matching: lowercase, non-alphanumerics -> single spaces."""
    return " " + re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (s or "").lower())).strip() + " "


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--release", default=None)
    ap.add_argument("--out", default="data/raw/overture_places.csv")
    args = ap.parse_args()
    release = args.release or latest_release()
    print(f"Overture release {release}")

    cats = {r["overture_category"] for r in csv.DictReader((SEEDS / "overture_category_map.csv").open(encoding="utf-8"))}
    terms = [r["term"] for r in csv.DictReader((SEEDS / "sport_search_terms.csv").open(encoding="utf-8"))]
    needles = [" " + t + " " for t in terms]

    con = duckdb.connect()
    con.execute("install httpfs; load httpfs; set s3_region='us-west-2';")
    path = f"s3://{BUCKET}/release/{release}/theme=places/type=place/*"
    # Pre-filter by category in SQL (cheap: only the taxonomy columns are read) and by name in Python.
    rows = con.execute(f"""
        select id, names.primary, taxonomy.primary, taxonomy.hierarchy[1], taxonomy.hierarchy[2],
               bbox.ymin, bbox.xmin, confidence, operating_status,
               websites[1], phones[1],
               addresses[1].freeform, addresses[1].locality, addresses[1].postcode, addresses[1].region,
               sources[1].license, sources[1].dataset
        from read_parquet('{path}', hive_partitioning=1)
        where bbox.xmin between -124.5 and -114.0 and bbox.ymin between 32.5 and 42.1
          and names.primary is not null
          and (taxonomy.hierarchy[1] = 'sports_and_recreation'
               or regexp_matches(coalesce(taxonomy.primary, ''),
                    'tennis|pickle|padel|squash|badminton|racquet|racket|recreation|athletic|country_club|community_center|sports'))
    """).fetchall()
    print(f"{len(rows):,} candidate places in sports/recreation categories (CA bounding box)")

    keep, outside = [], 0
    for r in rows:
        name_n = norm(r[1])
        if not (r[2] in cats or any(n in name_n for n in needles)):
            continue
        if not overpass.in_california(r[5], r[6]):
            outside += 1
            continue
        keep.append((*r, release))
    print(f"kept {len(keep):,} (racket category or sport word in the name); {outside:,} dropped outside the California border")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(FIELDS)
        w.writerows(keep)
    print(f"Wrote {len(keep):,} rows to {out}")


if __name__ == "__main__":
    main()
