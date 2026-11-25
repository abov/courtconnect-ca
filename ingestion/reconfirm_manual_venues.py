"""Re-read the pages behind hand-added venues that are going stale, and re-date only the rows whose page still names the place.

    python ingestion/reconfirm_manual_venues.py --dry-run     # what would change, nothing written
    python ingestion/reconfirm_manual_venues.py               # re-date rows in transform/seeds/manual_venues.csv
    python ingestion/reconfirm_manual_venues.py --older-than 28 --limit 200

Why: "Venues seen in the last 35 days" (target >= 99%) counts a hand-added venue as seen on its `confirmed_on`. Rows added in one
research pass all age out together, and a person re-reading hundreds of pages costs a session each time. This is the mechanical
part of that re-read: fetch the row's own `website` (public page, project User-Agent, one request per page, a pause per host) and
re-date the row only when the page text still names the venue AND its sport. Everything else stays stale on purpose (honesty rule):
a page that is gone, blocked (city sites often answer 403), JavaScript-only, or no longer names the place goes to the queue for a
person, `data/raw/reconfirm_queue.csv`. No model reads anything here, and nothing is inferred: a re-dated row says in `evidence`
exactly what was checked.

Matching: the venue name and the page are both folded (case, accents, punctuation, "&"/"and", "St"/"Saint"). A name matches when
the whole folded name is on the page, or every distinctive word of it is (generic words like park, courts, club, center are
dropped first; a name with no distinctive word left needs the whole name). The sport matches on its name or a common spelling
("pickle ball", "ping pong", "paddle" is NOT padel). Rows with no website are skipped: they need a person.
Run it from a home connection (the cloud sessions' network blocks most of these sites), then `make build` and `make app-data`.
"""
from __future__ import annotations

import argparse
import csv
import html
import io
import re
import time
import unicodedata
from collections import defaultdict
from datetime import date, timedelta
from urllib.parse import urlsplit

import requests
from rawdir import raw_path
from useragent import HEADERS as UA

SEED = "transform/seeds/manual_venues.csv"
PAUSE = 1.5            # seconds between requests to the same host
MAX_BYTES = 3_000_000
GENERIC = set("""the a an at of and in on de la el los las
park parks courts court club clubs center centre community recreation rec sports sport athletic athletics fitness
tennis pickleball padel squash racquetball badminton table pelota frontenis fronton beach pop platform paddle
complex facility facilities field fields gym gymnasium school high middle elementary college university campus
city county regional memorial public north south east west upper lower new old""".split())
SPORT_WORDS = {
    "pickleball": ["pickleball", "pickle ball"],
    "table tennis": ["table tennis", "ping pong", "ping-pong"],
    "padel": ["padel", "pádel"],
    "racquetball": ["racquetball", "racketball"],
}


def fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", html.unescape(s)).encode("ascii", "ignore").decode().lower()
    s = s.replace("&", " and ")
    s = re.sub(r"\bst\.?\s", "saint ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " " + re.sub(r"\s+", " ", s).strip() + " "


def page_text(body: bytes) -> str:
    s = body[:MAX_BYTES].decode("utf-8", errors="ignore")
    s = re.sub(r"(?is)<(script|style|noscript|svg)\b.*?</\1>", " ", s)
    title = " ".join(re.findall(r"(?is)<title[^>]*>(.*?)</title>", s))
    s = re.sub(r"(?s)<!--.*?-->", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    return fold(title + " " + s)


def name_on_page(name: str, text: str) -> bool:
    core = re.sub(r"\(.*?\)", " ", name)          # "(BT Cali Club, ...)" notes are ours, not the page's
    full = fold(core)
    if len(full.strip()) >= 4 and full in text:
        return True
    words = [w for w in full.split() if w not in GENERIC and len(w) > 1]
    return bool(words) and all(f" {w} " in text for w in words)


def sport_on_page(sport: str, text: str) -> bool:
    base = sport.split(":")[-1].strip().lower()   # "Basque Pelota: Frontenis" -> frontenis
    return any(fold(w) in text for w in SPORT_WORDS.get(base, [base]))


def fetch(url: str) -> tuple[str, str]:
    """(status, folded text). status: ok | http <code> | error <kind>."""
    try:
        r = requests.get(url, headers=UA, timeout=25, allow_redirects=True)
    except requests.RequestException as e:
        return f"error {type(e).__name__}", ""
    if r.status_code != 200:
        return f"http {r.status_code}", ""
    return "ok", page_text(r.content)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--older-than", type=int, default=28, help="re-read rows whose confirmed_on is older than this many days (blank counts)")
    ap.add_argument("--limit", type=int, default=0, help="read at most this many pages (0 = all due)")
    ap.add_argument("--dry-run", action="store_true", help="print what would change, write nothing")
    ap.add_argument("--queue", default=raw_path("reconfirm_queue.csv"))
    args = ap.parse_args()

    today = date.today()
    cutoff = (today - timedelta(days=args.older_than)).isoformat()
    raw = open(SEED, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.split(nl)
    reader = csv.reader(io.StringIO(raw, newline=""))
    header = next(reader)
    records = []                                 # (first line, line after last, row): a quoted field may span lines
    start = reader.line_num
    for fields in reader:
        if fields:
            records.append((start, reader.line_num, dict(zip(header, fields))))
        start = reader.line_num

    due = defaultdict(list)                      # url -> [(first line, end line, row)]
    no_site = 0
    for first, end, row in records:
        if row.get("confirmed_on") and row["confirmed_on"] >= cutoff:
            continue
        url = (row.get("website") or "").strip()
        if not url.startswith(("https://", "http://")):
            no_site += 1
            continue
        due[url].append((first, end, row))
    urls = sorted(due, key=lambda u: (urlsplit(u).netloc, u))
    if args.limit:
        urls = urls[: args.limit]
    print(f"{sum(len(due[u]) for u in urls)} rows on {len(urls)} pages due (confirmed before {cutoff}); {no_site} due rows have no website")

    last_hit: dict[str, float] = {}
    redated, queue = 0, []
    for n, url in enumerate(urls, 1):
        host = urlsplit(url).netloc
        wait = PAUSE - (time.monotonic() - last_hit.get(host, 0))
        if wait > 0:
            time.sleep(wait)
        status, text = fetch(url)
        last_hit[host] = time.monotonic()
        for first, end, row in due[url]:
            if status != "ok":
                reason = status
            elif not name_on_page(row["venue_name"], text):
                reason = "page no longer names the place (or is JavaScript-only)"
            elif not sport_on_page(row["sport"], text):
                reason = f"page names the place but not {row['sport']}"
            else:
                reason = ""
            if reason:
                queue.append({"venue_key": row["venue_key"], "venue_name": row["venue_name"], "sport": row["sport"],
                              "website": url, "confirmed_on": row["confirmed_on"], "reason": reason})
                continue
            row["confirmed_on"] = today.isoformat()
            note = f"Re-read {today.isoformat()} (reconfirm_manual_venues.py): the page still names the place and {row['sport']}."
            row["evidence"] = (row["evidence"].rstrip() + " " + note).strip()
            buf = io.StringIO()
            csv.writer(buf, lineterminator="").writerow([row[h] for h in header])
            lines[first] = buf.getvalue()                # only re-dated rows are rewritten; every other line stays byte-for-byte
            for j in range(first + 1, end):
                lines[j] = None
            redated += 1
        if n % 25 == 0:
            print(f"  {n}/{len(urls)} pages, {redated} rows re-dated so far")

    print(f"re-dated {redated} rows; {len(queue)} rows left for a person ({args.queue})")
    reasons = defaultdict(int)
    for q in queue:
        reasons[q["reason"].split(" (")[0] if q["reason"].startswith("page") else q["reason"]] += 1
    for k, v in sorted(reasons.items(), key=lambda kv: -kv[1]):
        print(f"  {v:4d}  {k}")
    if args.dry_run:
        print("dry run: nothing written")
        return
    open(SEED, "w", encoding="utf-8", newline="").write(nl.join(l for l in lines if l is not None))
    with open(args.queue, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["venue_key", "venue_name", "sport", "website", "confirmed_on", "reason"])
        w.writeheader()
        w.writerows(queue)
    if redated:
        print("next: make build (or build_changed.py), then make app-data, and commit both")


if __name__ == "__main__":
    main()
