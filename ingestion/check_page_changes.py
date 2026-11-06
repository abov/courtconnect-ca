"""Find the pages we rely on that CHANGED since we last looked, so a person or the page reader rechecks only those.

    python ingestion/check_page_changes.py                  # check pages not looked at in the last 30 days
    python ingestion/check_page_changes.py --max-age-days 0 --limit 50

Why: a verified venue goes stale silently, and rereading every page on a schedule costs more the bigger the map gets. A page that
did not change needs no recheck, so this asks the site first (a conditional request: ETag / Last-Modified) and compares a hash of the
visible text, and costs bandwidth only. No page is read by a model here; the output is a queue of pages worth a closer look.

Pages: every link-out in venue_actions.csv and every hand-added venue website (manual_venues.csv). Public pages only, one request per
page, a pause between requests to the same host, the project User-Agent.
Limit: a page whose text changes on every load (dates, counters, ads) reads as changed; after two changed checks in a row it is
marked 'volatile' and no longer queued. A JavaScript-only page hashes its empty shell, so it reads as unchanged; check_action_links.py
has the same blind spot.

Output: data/raw/page_checks.csv (url, status, etag, last_modified, text_hash, changed_runs, checked_at, first_seen)
  status: new | unchanged | changed | volatile | gone | error. The queue printed at the end is the changed and gone rows.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

import requests
from rawdir import raw_path
from useragent import HEADERS as UA

SEEDS = [("transform/seeds/venue_actions.csv", "url"), ("transform/seeds/manual_venues.csv", "website")]
FIELDS = ["url", "status", "etag", "last_modified", "text_hash", "changed_runs", "checked_at", "first_seen"]
PAUSE = 1.0              # seconds between requests to the same host
MAX_BYTES = 2_000_000    # never hash more than this much of a page


def page_urls() -> list[str]:
    urls = set()
    for path, col in SEEDS:
        with open(path, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                u = (r.get(col) or "").strip()
                if u.startswith("https://") or u.startswith("http://"):
                    urls.add(u)
    return sorted(urls)


def text_hash(body: bytes) -> str:
    """Hash of the visible text: scripts, styles and tags removed, whitespace and case folded."""
    s = body[:MAX_BYTES].decode("utf-8", errors="ignore")
    s = re.sub(r"(?is)<(script|style|noscript|svg)\b.*?</\1>", " ", s)
    s = re.sub(r"(?s)<!--.*?-->", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", html.unescape(s)).strip().lower()
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def check(url: str, prev: dict | None) -> dict:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    first = prev["first_seen"] if prev else now
    row = {"url": url, "status": "error", "etag": "", "last_modified": "", "text_hash": prev["text_hash"] if prev else "",
           "changed_runs": prev["changed_runs"] if prev else "0", "checked_at": now, "first_seen": first}
    headers = dict(UA)
    if prev and prev["status"] != "error":
        if prev["etag"]:
            headers["If-None-Match"] = prev["etag"]
        if prev["last_modified"]:
            headers["If-Modified-Since"] = prev["last_modified"]
    try:
        r = requests.get(url, headers=headers, timeout=25, allow_redirects=True)
    except requests.RequestException:
        return row
    if r.status_code == 304:
        return {**row, "status": "unchanged", "etag": prev["etag"], "last_modified": prev["last_modified"], "changed_runs": "0"}
    if r.status_code in (404, 410):
        return {**row, "status": "gone"}
    if r.status_code != 200:
        return row                       # 403, 429, 5xx: inconclusive, never read as a change
    h = text_hash(r.content)
    row.update(etag=r.headers.get("ETag", ""), last_modified=r.headers.get("Last-Modified", ""), text_hash=h)
    if not prev or not prev["text_hash"]:
        return {**row, "status": "new", "changed_runs": "0"}
    if h == prev["text_hash"]:
        return {**row, "status": "unchanged", "changed_runs": "0"}
    runs = int(prev["changed_runs"] or 0) + 1
    return {**row, "status": "volatile" if runs >= 2 else "changed", "changed_runs": str(runs)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=raw_path("page_checks.csv"))
    ap.add_argument("--max-age-days", type=int, default=30, help="skip pages checked more recently than this")
    ap.add_argument("--limit", type=int, default=0, help="check at most this many pages (0 = all due)")
    args = ap.parse_args()

    out = Path(args.out)
    previous: dict[str, dict] = {}
    if out.exists():
        with out.open(encoding="utf-8", newline="") as f:
            previous = {r["url"]: r for r in csv.DictReader(f)}
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.max_age_days)

    def due(u: str) -> bool:
        p = previous.get(u)
        try:
            return not p or datetime.fromisoformat(p["checked_at"]) <= cutoff
        except (KeyError, ValueError):
            return True

    urls = page_urls()
    todo = [u for u in urls if due(u)]
    todo.sort(key=lambda u: previous[u]["checked_at"] if u in previous else "")     # never-checked first, then oldest
    if args.limit:
        todo = todo[:args.limit]
    print(f"{len(urls):,} pages; {len(todo):,} due")

    last_hit: dict[str, float] = {}
    results = {}
    for u in todo:
        host = urlsplit(u).hostname or ""
        wait = PAUSE - (time.monotonic() - last_hit.get(host, -PAUSE))
        if wait > 0:
            time.sleep(wait)
        results[u] = check(u, previous.get(u))
        last_hit[host] = time.monotonic()

    merged = {u: r for u, r in {**previous, **results}.items() if u in set(urls)}      # drop pages no longer used anywhere
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(merged[u] for u in sorted(merged))

    counts: dict[str, int] = {}
    for r in results.values():
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print("checked:", ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) or "nothing due")
    queue = [r for r in results.values() if r["status"] in ("changed", "gone")]
    if queue:
        print("\nRecheck these (changed or gone):")
        for r in queue:
            print(f"  {r['status']:<8} {r['url']}")


if __name__ == "__main__":
    main()
