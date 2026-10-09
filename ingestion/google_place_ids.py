"""Resolve our venues to Google place IDs (and store ONLY the IDs).

Why only IDs: Google's Places API policy forbids storing Places content (names, addresses, coordinates, phone numbers,
hours...) beyond narrow exceptions, but explicitly lets you store place IDs indefinitely. So this script asks Google for the
single field `places.id`, saves venue_id -> place ID, and never writes anything else Google returns. An app can then call
Place Details with the stored ID at display time. See docs/decisions/0005-overture-places-and-google-terms.md.

SAFE BY DEFAULT. Without --execute nothing is sent: you get a plan (how many requests, which venues).

    python ingestion/google_place_ids.py                      # dry run: plan only, no network, no key needed
    python ingestion/google_place_ids.py --execute --limit 20 # real run (needs GOOGLE_PLACES_API_KEY in .env)

Cost: each venue is one Text Search request. Check Google's current Places API pricing for the "IDs Only" SKU and your
free monthly allowance before raising --limit; this script enforces --max-requests as a hard ceiling either way.

Output: data/raw/google_place_ids.csv  (venue_id, google_place_id, resolved_at). Re-runs skip venues already resolved.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import requests
from dotenv import load_dotenv

BASE_URL = os.environ.get("GOOGLE_PLACES_BASE_URL", "https://places.googleapis.com")  # overridable for tests
FIELDS = ["venue_id", "google_place_id", "resolved_at"]
BIAS_RADIUS_M = 500.0


def candidates(db: str, scope: str) -> list[dict]:
    """Venues worth resolving: those with a real name, best-documented first."""
    names = {"confirmed": "('court_name', 'operator', 'places_directory')",
             "all-named": "('court_name', 'operator', 'places_directory', 'enclosing_feature')"}[scope]
    con = duckdb.connect(db, read_only=True)
    rows = con.execute(f"""
        select v.venue_id, v.venue_name, v.city, v.lat, v.lon, count(distinct bvs.sport_id) as sports
        from core.dim_venue v
        join core.bridge_venue_sport bvs on bvs.venue_id = v.venue_id
        where v.name_source in {names} and v.venue_name is not null
        group by 1, 2, 3, 4, 5
        order by sports desc, v.venue_name
    """).fetchall()
    return [dict(zip(["venue_id", "name", "city", "lat", "lon", "sports"], r)) for r in rows]


def already_done(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open(encoding="utf-8", newline="") as f:
        return {r["venue_id"] for r in csv.DictReader(f)}


def lookup(session: requests.Session, key: str, v: dict) -> str | None:
    q = f"{v['name']} {v['city'] or ''}".strip()
    body = {"textQuery": q, "pageSize": 1,
            "locationBias": {"circle": {"center": {"latitude": v["lat"], "longitude": v["lon"]}, "radius": BIAS_RADIUS_M}}}
    r = session.post(f"{BASE_URL}/v1/places:searchText", json=body, timeout=30,
                     headers={"X-Goog-Api-Key": key, "X-Goog-FieldMask": "places.id"})  # ask for the ID and nothing else
    if r.status_code in (401, 403):
        raise SystemExit(f"Google rejected the key or the API is not enabled ({r.status_code}). Stopping.")
    if r.status_code == 429:
        raise SystemExit("Rate limited by Google (429). Stopping; re-run later (finished venues are skipped).")
    r.raise_for_status()
    places = r.json().get("places") or []
    return places[0]["id"] if places else None  # keep only the ID, discard everything else


def main() -> None:
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true", help="actually call Google (default: dry run)")
    ap.add_argument("--limit", type=int, default=25, help="venues to resolve this run")
    ap.add_argument("--max-requests", type=int, default=100, help="hard ceiling on API calls, whatever --limit says")
    ap.add_argument("--scope", choices=["confirmed", "all-named"], default="confirmed")
    ap.add_argument("--db", default="courtconnect.duckdb")
    ap.add_argument("--out", default="data/raw/google_place_ids.csv")
    ap.add_argument("--price-per-1000", type=float, default=None, help="USD per 1,000 requests, from Google's pricing page (for the estimate)")
    args = ap.parse_args()

    out = Path(args.out)
    todo = [v for v in candidates(args.db, args.scope) if v["venue_id"] not in already_done(out)]
    n = min(args.limit, args.max_requests, len(todo))
    print(f"{len(todo):,} venues still unresolved in scope '{args.scope}'; this run would send {n} request(s).")
    if args.price_per_1000 is not None:
        print(f"Estimated cost at ${args.price_per_1000}/1,000 requests: ${n * args.price_per_1000 / 1000:,.2f}")

    if not args.execute:
        print("\nDRY RUN: nothing sent. First venues in the plan:")
        for v in todo[:n][:8]:
            print(f"  {v['name']} ({v['city'] or 'n/a'})  [{v['sports']} sport(s)]")
        print("\nTo run for real: add your key as GOOGLE_PLACES_API_KEY in .env, then re-run with --execute.")
        return

    key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not key:
        sys.exit("GOOGLE_PLACES_API_KEY is not set (put it in .env, which is gitignored).")

    out.parent.mkdir(parents=True, exist_ok=True)
    new_file = not out.exists()
    sent = found = 0
    with out.open("a", encoding="utf-8", newline="") as f, requests.Session() as session:
        w = csv.writer(f)
        if new_file:
            w.writerow(FIELDS)
        for v in todo[:n]:
            if sent >= args.max_requests:
                break
            pid = lookup(session, key, v)
            sent += 1
            if pid:
                found += 1
                w.writerow([v["venue_id"], pid, datetime.now(timezone.utc).isoformat(timespec="seconds")])
                f.flush()
            time.sleep(0.2)
    print(f"Sent {sent} request(s); resolved {found} place ID(s) -> {out}")


if __name__ == "__main__":
    main()
