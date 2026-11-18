"""Find official websites for pins that have none, with scripts first and a model only for what is left.

The repeated "official websites for N pins" research passes (PRs #822-#840) spent a large model on work that is mostly
mechanical: list the pins with no website, find a candidate page, check the page names the place, write the seed row.
This script does the mechanical part and leaves only the ambiguous rows for a cheap model (docs/website_finder.md).

    python ingestion/find_websites.py --region OR --city Portland,Beaverton --sport Tennis        # real run
    python ingestion/find_websites.py --region OR --city Portland --eval                          # measure against the seed
    python ingestion/find_websites.py --bbox 45.3,-123.1,45.7,-122.3 --max-pins 40 --dry-run      # list pins, no HTTP

Steps (every outside request sends the project User-Agent only, ingestion/useragent.py; robots.txt is respected; public pages only):
 1. List candidate pins from the warehouse (mart_venue_finder + dim_venue): named, not home-like, no website from OSM,
    Overture, manual_venues or venue_website_official; filtered by region / city / bbox / sport.
 2. Propose candidate URLs, cheapest first:  a) --hints file (url per venue_id, from a person or a model's web search);
    b) Overture places within 300 m that have a website; c) Wikidata entities with the same name and a coordinate within
    2 km (official website property, CC0); d) sibling pattern: schools of one district share a host suffix, so
    <slug>.<suffix> is tried for the suffixes known nearby (DNS first, so a wrong guess costs nothing).
 3. Fetch each candidate with plain HTTP (redirects followed, 400 KB cap, one host at a time) and score it by code:
    every distinctive word of the pin name in the page title / first heading / site name, a place word (school type, club,
    college) never contradicting, the pin's city, street or ZIP on the page, no social / listing / directory host.
 4. Write three files to data/website_proposals/ (git-ignored):
      proposed_rows.csv   venue_id,lat,lon,website,evidence,verified_on in the exact seed shape; confidence "auto" rows only
      review_queue.csv    everything else that had a candidate or none: pin facts, best candidate, the failed checks and a
                          trimmed page extract, so a model reads ~1 KB per row instead of searching from scratch
      report.md           counts per stage
    --apply appends proposed_rows.csv to transform/seeds/venue_website_official.csv (CRLF, no duplicate venue_id).

The model is never the source of truth for an "auto" row and never sees one. A row that needs a model is not in the seed until
a person or the model's answer has been through the same page checks (--hints re-runs them).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html as htmllib
import json
import math
import re
import socket
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import duckdb
import requests

from page_reader import html_to_text, robots_allows
from rawdir import ROOT, raw_dir
from useragent import USER_AGENT

DB = ROOT / "courtconnect.duckdb"
SEED = ROOT / "transform" / "seeds" / "venue_website_official.csv"
OUT_DIR = ROOT / "data" / "website_proposals"
CACHE_DIR = raw_dir().parent / "reader_cache"
CACHE_DAYS = 14
MAX_BYTES = 400_000
SEED_FIELDS = ["venue_id", "lat", "lon", "website", "evidence", "verified_on"]
REVIEW_FIELDS = ["venue_id", "venue_name", "city", "region", "lat", "lon", "address_line", "best_url", "source", "score",
                 "failed_checks", "page_title", "page_extract", "other_urls"]

GENERIC = {"the", "of", "and", "at", "a", "an", "for", "in", "tennis", "court", "courts", "pickleball", "park", "parks", "center",
           "centre", "recreation", "rec", "playground", "field", "fields", "complex", "facility", "gym", "gymnasium", "sports",
           "county", "city", "community", "public", "open", "play", "area", "tc", "courts."}
# A name word that says what kind of place it is. These are required to match when the pin has one (high != middle).
KIND_WORDS = {"high": "school", "middle": "school", "elementary": "school", "junior": "school", "intermediate": "school",
              "primary": "school", "academy": "school", "school": "school", "college": "college", "university": "college",
              "club": "club", "resort": "resort", "hotel": "resort"}
EXCLUDED_HOSTS = ("facebook.", "instagram.", "twitter.", "x.com", "youtube.", "yelp.", "tripadvisor.", "mapquest.", "google.", "bing.",
                  "wikipedia.", "wikimedia.", "linkedin.", "tiktok.", "nextdoor.", "yellowpages.", "foursquare.", "tennisround.",
                  "playtomic.", "pickleheads.", "courtreserve.", "usta.com", "greatschools.", "niche.com", "schooldigger.",
                  "publicschoolreview.", "usnews.", "ratemyprofessors.", "zillow.", "redfin.", "apartments.", "loopnet.")
ALIASES = {"st": "saint", "mt": "mount", "ft": "fort", "jr": "junior", "sr": "senior", "hs": "high", "ms": "middle", "es": "elementary"}
STATE_NAMES = {"CA": ("california", "ca"), "NV": ("nevada", "nv"), "OR": ("oregon", "or"), "WA": ("washington", "wa"),
               "AZ": ("arizona", "az"), "NM": ("new mexico", "nm"), "HI": ("hawaii", "hi"), "TX": ("texas", "tx")}

_lock = threading.Lock()
_last_hit: dict[str, float] = {}
HOST_DELAY_S = 2.0


# ---------- text helpers ----------
def words(s: str) -> list[str]:
    s = htmllib.unescape(s or "").lower().replace("&", " and ")
    s = re.sub(r"[’'`]", "", s)
    out = []
    for w in re.findall(r"[a-z0-9]+", s):
        out.append(ALIASES.get(w, w))
    return out


def clean_name(name: str) -> str:
    """Display names carry suffixes the page will not: '(northeast courts, 2 courts)', ' - Gresham', ' at Marshall Campus', 'Tennis Courts'."""
    n = re.sub(r"\s*\(.*?\)", "", name or "")
    n = re.split(r"\s+-\s+|\s+at\s+|\s*,\s*", n)[0]
    return re.sub(r"\s+(tennis|pickleball)?\s*courts?$", "", n, flags=re.I).strip() or name


def distinctive(name: str) -> list[str]:
    ws = [w for w in words(name) if w not in GENERIC]
    return list(dict.fromkeys(ws))


def host_of(url: str) -> str:
    h = (urlsplit(url).hostname or "").lower()
    return h[4:] if h.startswith("www.") else h


def bad_host(url: str) -> bool:
    h = host_of(url) + "/"
    return any(x in h for x in EXCLUDED_HOSTS)


def haversine_m(a_lat, a_lon, b_lat, b_lon) -> float:
    p = math.pi / 180
    d = math.sin((b_lat - a_lat) * p / 2) ** 2 + math.cos(a_lat * p) * math.cos(b_lat * p) * math.sin((b_lon - a_lon) * p / 2) ** 2
    return 12742000 * math.asin(math.sqrt(d))


# ---------- http ----------
def _wait_host(host: str) -> None:
    with _lock:
        wait = HOST_DELAY_S - (time.time() - _last_hit.get(host, 0))
        _last_hit[host] = time.time() + max(wait, 0)
    if wait > 0:
        time.sleep(wait)


def _cache_path(key: str) -> Path:
    return CACHE_DIR / ("find_" + hashlib.sha1(key.encode()).hexdigest() + ".json")


def fetch_page(url: str) -> dict:
    """{'url', 'final_url', 'status', 'title', 'h1', 'site_name', 'text'}; status ok | robots | http_<n> | error | not_html."""
    cp = _cache_path(url)
    if cp.exists():
        c = json.loads(cp.read_text(encoding="utf-8"))
        if date.fromisoformat(c["fetched_on"]) >= date.today() - timedelta(days=CACHE_DAYS):
            return c
    out = {"url": url, "final_url": url, "status": "error", "title": "", "h1": "", "site_name": "", "text": "",
           "fetched_on": date.today().isoformat()}
    try:
        if not robots_allows(url):
            out["status"] = "robots"
        else:
            _wait_host(host_of(url))
            r = requests.get(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"}, timeout=(8, 20), stream=True,
                             allow_redirects=True)
            body = r.raw.read(MAX_BYTES, decode_content=True) if r.status_code == 200 else b""
            r.close()
            ctype = r.headers.get("content-type", "")
            out["final_url"] = r.url
            if r.status_code != 200:
                out["status"] = f"http_{r.status_code}"
            elif "html" not in ctype and "text" not in ctype:
                out["status"] = "not_html"
            else:
                enc = r.encoding or "utf-8"
                raw = body.decode(enc, errors="ignore")
                m = re.search(r"(?is)<title[^>]*>(.*?)</title>", raw)
                out["title"] = re.sub(r"\s+", " ", htmllib.unescape(m.group(1))).strip() if m else ""
                m = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", raw)
                out["h1"] = re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", m.group(1)))).strip() if m else ""
                m = re.search(r'(?is)<meta[^>]+property=["\']og:site_name["\'][^>]+content=["\']([^"\']+)', raw)
                out["site_name"] = htmllib.unescape(m.group(1)).strip() if m else ""
                out["text"] = html_to_text(raw)[:20000]
                out["status"] = "ok"
    except (requests.RequestException, OSError, ValueError):
        out["status"] = "error"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cp.write_text(json.dumps(out), encoding="utf-8")
    return out


def fetch_with_fallback(url: str) -> dict:
    """A candidate that fails (stale deep link, robots on a script path) is retried at the site root over https."""
    page = fetch_page(url)
    if page["status"] == "ok":
        return page
    sp = urlsplit(url)
    root = f"https://{sp.netloc}/"
    if root != url:
        alt = fetch_page(root)
        if alt["status"] == "ok":
            return alt
    return page


def dns_ok(host: str) -> bool:
    try:
        socket.getaddrinfo(host, None)
        return True
    except OSError:
        return False


def get_json(url: str, params: dict) -> dict | None:
    key = url + json.dumps(params, sort_keys=True)
    cp = _cache_path(key)
    if cp.exists():
        c = json.loads(cp.read_text(encoding="utf-8"))
        if date.fromisoformat(c["fetched_on"]) >= date.today() - timedelta(days=CACHE_DAYS):
            return c["data"]
    _wait_host(host_of(url))
    try:
        r = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=20)
        data = r.json() if r.status_code == 200 else None
    except (requests.RequestException, ValueError):
        return None
    if data is not None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cp.write_text(json.dumps({"fetched_on": date.today().isoformat(), "data": data}), encoding="utf-8")
    return data


# ---------- step 1: pins ----------
def list_pins(a: argparse.Namespace) -> list[dict]:
    con = duckdb.connect(str(DB), read_only=True)
    where = ["f.venue_kind = 'courts'", "f.sport_name = ?", "coalesce(f.is_home_like, false) = false",
             "f.venue_name is not null", "f.venue_name not like 'Unnamed%'", "f.name_source <> 'unnamed'"]
    params: list = [a.sport]
    if not a.eval:
        where.append("f.website is null")
    if a.region:
        where.append("f.region = ?")
        params.append(a.region)
    if a.city:
        cities = [c.strip().lower() for c in a.city.split(",") if c.strip()]
        where.append("lower(f.city) in (" + ",".join("?" * len(cities)) + ")")
        params += cities
    if a.bbox:
        s, w, n, e = a.bbox
        where.append("f.lat between ? and ? and f.lon between ? and ?")
        params += [s, n, w, e]
    seed_ids = set()
    if SEED.exists():
        with SEED.open(encoding="utf-8", newline="") as fh:
            seed_ids = {r["venue_id"] for r in csv.DictReader(fh)}
    sql = f"""select distinct f.venue_id, f.venue_name, f.name_source, f.city, f.region, f.lat, f.lon, f.address_line, f.website,
                     f.courts_for_sport
              from marts.mart_venue_finder f where {' and '.join(where)} order by f.region, f.city, f.venue_name"""
    rows = [dict(zip(["venue_id", "venue_name", "name_source", "city", "region", "lat", "lon", "address_line", "website", "courts"], r))
            for r in con.execute(sql, params).fetchall()]
    if a.eval:      # evaluation: only pins a past pass already settled, treated as if they had no website
        rows = [r for r in rows if r["venue_id"] in seed_ids]
    else:
        rows = [r for r in rows if r["venue_id"] not in seed_ids]
    for r in rows:
        r["display_name"], r["venue_name"] = r["venue_name"], clean_name(r["venue_name"])
    if a.max_pins:
        rows = rows[: a.max_pins]
    return rows


def known_sites(con, lat: float, lon: float, exclude: set[str], radius_deg: float = 0.2) -> list[tuple[str, float, float, str]]:
    rows = con.execute("""select website, lat, lon, venue_name, venue_id from marts.mart_venue_finder
                          where website is not null and lat between ? and ? and lon between ? and ?""",
                       [lat - radius_deg, lat + radius_deg, lon - radius_deg, lon + radius_deg]).fetchall()
    return [r[:4] for r in rows if r[4] not in exclude]


# ---------- step 2: candidates ----------
def slugs_for(name: str) -> list[str]:
    ws = [w for w in words(name) if w not in {"the", "of", "and"}]
    core = [w for w in ws if w not in KIND_WORDS and w not in GENERIC]
    out = []
    if core:
        out.append(core[0])
        out.append("".join(core))
    initials = "".join(w[0] for w in ws if w not in GENERIC)
    if len(initials) >= 2:
        out.append(initials)
    if core:
        kinds = [w for w in ws if w in KIND_WORDS]
        if kinds:
            out.append(core[0] + kinds[0][0])
    return list(dict.fromkeys(s for s in out if len(s) >= 2))


def candidates_for(pin: dict, con, a: argparse.Namespace, hints: dict[str, list[str]], exclude: set[str], directory: list[dict]) -> list[tuple[str, str]]:
    """[(url, source)] best first; geo-anchored sources first."""
    out: list[tuple[str, str]] = [(u, "hint") for u in hints.get(pin["venue_id"], [])]
    # a2) a public directory a person downloaded: same cleaned name, same city
    dw = distinctive(pin["venue_name"])
    for r in directory:
        if r["city"].strip().lower() == (pin["city"] or "").lower() and distinctive(r["name"]) == dw and r["website"].strip():
            out.append((r["website"].strip(), "directory"))
    # b) Overture places within 300 m with a website and a matching name
    d = 0.003
    for site, lat, lon, nm in con.execute(
            """select website, lat, lon, place_name from staging.stg_overture_places
               where website is not null and lat between ? and ? and lon between ? and ?""",
            [pin["lat"] - d, pin["lat"] + d, pin["lon"] - d, pin["lon"] + d]).fetchall():
        dw = set(distinctive(pin["venue_name"]))
        if dw and dw <= set(words(nm)) and haversine_m(pin["lat"], pin["lon"], lat, lon) <= 300:
            out.append((site, "overture_near"))
    # c) Wikidata
    if not a.no_wikidata:
        out += wikidata_candidates(pin)
    # d) district / suffix sibling pattern
    if not a.no_guess:
        out += pattern_candidates(pin, con, exclude)
    seen, dedup = set(), []
    for u, s in out:
        k = host_of(u) + urlsplit(u).path.rstrip("/")
        if k not in seen and not bad_host(u):
            seen.add(k)
            dedup.append((u, s))
    return dedup[: a.max_candidates]


def wikidata_candidates(pin: dict) -> list[tuple[str, str]]:
    api = "https://www.wikidata.org/w/api.php"
    s = get_json(api, {"action": "wbsearchentities", "search": pin["venue_name"], "language": "en", "limit": 5, "format": "json"})
    ids = [h["id"] for h in (s or {}).get("search", [])]
    if not ids:
        return []
    ents = get_json(api, {"action": "wbgetentities", "ids": "|".join(ids), "props": "claims|labels", "languages": "en", "format": "json"})
    out = []
    for e in (ents or {}).get("entities", {}).values():
        cl = e.get("claims", {})
        site = next((c["mainsnak"]["datavalue"]["value"] for c in cl.get("P856", []) if "datavalue" in c.get("mainsnak", {})), None)
        co = next((c["mainsnak"]["datavalue"]["value"] for c in cl.get("P625", []) if "datavalue" in c.get("mainsnak", {})), None)
        if site and co and haversine_m(pin["lat"], pin["lon"], co["latitude"], co["longitude"]) <= 2000:
            out.append((site, "wikidata"))
    return out


def pattern_candidates(pin: dict, con, exclude: set[str]) -> list[tuple[str, str]]:
    """Schools and colleges of one district share a host suffix (jackson.pps.net, bhs.beaverton.k12.or.us)."""
    ws = set(words(pin["venue_name"]))
    if not ws & set(KIND_WORDS):
        return []
    suffixes: Counter = Counter()
    for site, lat, lon, nm in known_sites(con, pin["lat"], pin["lon"], exclude):
        if not set(words(nm)) & set(KIND_WORDS):
            continue
        h = host_of(site)
        parts = h.split(".")
        if len(parts) >= 3 and haversine_m(pin["lat"], pin["lon"], lat, lon) <= 25000:
            suffixes[".".join(parts[1:])] += 1
    out = []
    for suffix, n in suffixes.most_common(3):
        if n < 2:
            continue
        for slug in slugs_for(pin["venue_name"]):
            host = f"{slug}.{suffix}"
            if dns_ok(host):
                out.append((f"https://{host}/", f"pattern:{suffix}"))
    return out


# ---------- step 3: score ----------
def score(pin: dict, page: dict, source: str) -> dict:
    """Return {'score': 0..1, 'tier': 'auto'|'review'|'reject', 'failed': [...], 'facts': {...}}."""
    failed: list[str] = []
    if page["status"] != "ok":
        return {"score": 0.0, "tier": "reject", "failed": [f"fetch:{page['status']}"], "facts": {}}
    head = " ".join([page["title"], page["h1"], page["site_name"], host_of(page["final_url"]).replace("-", " ").replace(".", " ")])
    head_words = set(words(head))
    body_words = set(words(page["text"][:6000]))
    need = distinctive(pin["venue_name"])
    core = [w for w in need if w not in KIND_WORDS] or need      # a missing place-kind word ("College") is tolerated when the rest matches
    in_head = [w for w in core if w in head_words]
    in_body = [w for w in core if w in body_words]
    s = 0.0
    if core:
        s += 0.5 * len(in_head) / len(core) + 0.1 * len(in_body) / len(core)
    missing = [w for w in core if w not in head_words]
    if missing:
        failed.append("name:" + ",".join(missing))
    levels = {"high", "middle", "elementary", "junior", "intermediate", "primary"}
    if any(w in levels and w not in head_words for w in need):
        failed.append("level:" + ",".join(w for w in need if w in levels and w not in head_words))   # a district page is not a school page
    if any(w in KIND_WORDS and w not in head_words for w in need):
        s -= 0.05
    # the kind of place must not contradict (Lakeridge High vs Lakeridge Middle)
    pin_kinds = {w for w in words(pin["venue_name"]) if w in KIND_WORDS}
    head_kinds = {w for w in head_words if w in KIND_WORDS}
    if pin_kinds and head_kinds and not (pin_kinds & head_kinds) and not {KIND_WORDS[k] for k in pin_kinds} == {KIND_WORDS[k] for k in head_kinds}:
        failed.append(f"kind:{'/'.join(sorted(pin_kinds))}!={'/'.join(sorted(head_kinds))}")
    elif pin_kinds & {"high", "middle", "elementary", "junior", "intermediate", "primary"} and head_kinds & {"high", "middle", "elementary", "junior", "intermediate", "primary"} \
            and not (pin_kinds & head_kinds):
        failed.append("kind:school level differs")
    # location: city, ZIP or street number + street word on the page
    text_l = page["text"].lower()
    loc = []
    if pin.get("city") and pin["city"].lower() in text_l:
        loc.append("city")
    st = STATE_NAMES.get(pin.get("region") or "", ())
    addr = (pin.get("address_line") or "")
    m = re.match(r"\s*(\d+)\s+(.*)", addr)
    if m:
        street_word = next((w for w in words(m.group(2)) if len(w) > 2 and w not in {"north", "south", "east", "west", "avenue", "street", "road", "drive", "boulevard", "lane", "way", "court"}), None)
        if street_word and re.search(rf"\b{m.group(1)}\b[^\n]{{0,40}}\b{street_word}", text_l):
            loc.append("street")
    if source in ("wikidata", "overture_near", "directory"):
        loc.append(source)
    if source.startswith("hint"):
        pass
    if loc:
        s += 0.3
    else:
        failed.append("location:not on page")
    if "tennis" in text_l:
        s += 0.1
    if source in ("wikidata", "overture_near", "directory"):
        s += 0.1
    if host_of(page["final_url"]) != host_of(page["url"]) and not host_of(page["final_url"]).endswith(host_of(page["url"]).split(".", 1)[-1]):
        failed.append(f"redirect:{host_of(page['final_url'])}")
        s -= 0.2
    # A park is run by a city, county or district: a .com page named after the park (fan site, tourism page, listing) goes to review.
    if not pin_kinds and re.search(r"\bpark\b|\bplayground\b", pin["venue_name"].lower()):
        h = host_of(page["final_url"])
        if not (h.endswith(".gov") or h.endswith(".us") or ".gov." in h or h.startswith(("cityof", "ci.", "co."))):
            failed.append("host:park page is not on a government domain")
    s = max(0.0, min(1.0, s))
    tier = "auto" if not failed and s >= 0.85 else ("review" if in_head else "reject")
    return {"score": round(s, 2), "tier": tier, "failed": failed,
            "facts": {"loc": loc, "tennis_on_page": "tennis" in text_l, "title": page["title"], "final_url": page["final_url"]}}


# ---------- step 4: output ----------
def kind_phrase(name: str) -> str:
    ks = {KIND_WORDS[w] for w in words(name) if w in KIND_WORDS}
    for k in ("college", "school", "club", "resort"):
        if k in ks:
            return k
    return "venue" if not re.search(r"\bpark\b", name.lower()) else "park"


def evidence_for(pin: dict, url: str, res: dict, source: str, today: str) -> str:
    f = res["facts"]
    kind = kind_phrase(pin["venue_name"])
    where = f"{pin['city']}, {pin['region']}" if pin.get("city") else pin["region"]
    tennis = "the page mentions tennis" if f["tennis_on_page"] else "the page does not mention tennis, court access is not confirmed by it"
    return (f"Official site {url} (fetched {today}, page title '{f['title']}'): official {kind} website. Pin is the court group named "
            f"'{pin['venue_name']}' in {where}; website is the homepage, not a tennis page; {tennis}. Proposed by ingestion/find_websites.py: "
            f"name match in title, location match ({'+'.join(f['loc'])}), candidate source {source}, score {res['score']}.")


def extract_for(page: dict, n: int = 500) -> str:
    return re.sub(r"\s+", " ", page["text"][:n])


def append_seed(rows: list[dict]) -> int:
    with SEED.open(encoding="utf-8", newline="") as fh:
        have = {r["venue_id"] for r in csv.DictReader(fh)}
    new = [r for r in rows if r["venue_id"] not in have]
    if not new:
        return 0
    with SEED.open("a", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=SEED_FIELDS, lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)
        for r in new:
            w.writerow({k: r[k] for k in SEED_FIELDS})
    return len(new)


def load_hints(path: str | None) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    if path:
        with open(path, encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                out.setdefault(r["venue_id"], []).append(r["url"].strip())
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--region", help="region code from ingestion/regions.json (CA, OR, ...)")
    ap.add_argument("--city", help="comma-separated city names as the map shows them")
    ap.add_argument("--bbox", type=float, nargs=4, metavar=("S", "W", "N", "E"))
    ap.add_argument("--sport", default="Tennis")
    ap.add_argument("--max-pins", type=int, default=0)
    ap.add_argument("--max-candidates", type=int, default=4, help="candidate URLs fetched per pin")
    ap.add_argument("--hints", help="csv venue_id,url: candidate pages from a person or a model's search; checked like any other")
    ap.add_argument("--no-wikidata", action="store_true")
    ap.add_argument("--no-guess", action="store_true", help="skip the district host-pattern guesses")
    ap.add_argument("--dry-run", action="store_true", help="list the pins and stop (no outside request)")
    ap.add_argument("--eval", action="store_true", help="re-find the sites of pins already in the seed and compare (precision/recall of the script)")
    ap.add_argument("--apply", action="store_true", help="append the auto rows to transform/seeds/venue_website_official.csv")
    ap.add_argument("--cold", action="store_true", help="with --eval: hide every evaluated pin's seed site from the sibling-pattern step too (cold start)")
    ap.add_argument("--directory", help="csv name,city,website from a public school/club directory (e.g. the CDE school list): matched by name + city")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()

    pins = list_pins(a)
    print(f"{len(pins)} candidate pins (sport {a.sport}, region {a.region or 'any'}, city {a.city or 'any'})")
    if a.dry_run or not pins:
        for p in pins[:50]:
            print(f"  {p['venue_id'][:8]}  {p['venue_name']}  ({p['city']}, {p['region']})")
        return 0
    hints = load_hints(a.hints)
    directory = []
    if a.directory:
        with open(a.directory, encoding="utf-8", newline="") as fh:
            directory = list(csv.DictReader(fh))
    exclude = {p["venue_id"] for p in pins} if a.eval and a.cold else set()   # --eval alone is leave-one-out: sibling pins' seeds stay known, the pin's own is hidden
    today = date.today().isoformat()
    seed_site = {}
    if a.eval:
        with SEED.open(encoding="utf-8", newline="") as fh:
            seed_site = {r["venue_id"]: r["website"] for r in csv.DictReader(fh)}

    def work(pin: dict) -> dict:
        con = duckdb.connect(str(DB), read_only=True)
        cands = candidates_for(pin, con, a, hints, exclude | {pin["venue_id"]}, directory)
        con.close()
        results = []
        for url, source in cands:
            page = fetch_with_fallback(url)
            r = score(pin, page, source)
            results.append({"url": page.get("final_url") or url, "source": source, "page": page, "res": r})
            if r["tier"] == "auto":
                break
        results.sort(key=lambda x: -x["res"]["score"])
        return {"pin": pin, "cands": results}

    with ThreadPoolExecutor(a.workers) as ex:
        done = list(ex.map(work, pins))

    proposed, review = [], []
    stats = Counter()
    for d in done:
        pin, cands = d["pin"], d["cands"]
        best = cands[0] if cands else None
        if best and best["res"]["tier"] == "auto":
            url = best["url"] if host_of(best["url"]) == host_of(best["page"]["url"]) else best["page"]["url"]
            proposed.append({"venue_id": pin["venue_id"], "lat": pin["lat"], "lon": pin["lon"], "website": url,
                             "evidence": evidence_for(pin, url, best["res"], best["source"], today), "verified_on": today})
            stats["auto"] += 1
            if a.eval:
                same = host_of(url) == host_of(seed_site.get(pin["venue_id"], ""))
                stats["eval_auto_same_host_as_seed" if same else "eval_auto_DIFFERENT_from_seed"] += 1
        else:
            stats["review_with_candidate" if best and best["res"]["tier"] == "review" else
                  ("no_page_passed" if best else "no_candidate")] += 1
            review.append({"venue_id": pin["venue_id"], "venue_name": pin["venue_name"], "city": pin["city"], "region": pin["region"],
                           "lat": pin["lat"], "lon": pin["lon"], "address_line": pin["address_line"],
                           "best_url": best["url"] if best else "", "source": best["source"] if best else "",
                           "score": best["res"]["score"] if best else "", "failed_checks": "; ".join(best["res"]["failed"]) if best else "no candidate url",
                           "page_title": best["page"]["title"] if best else "", "page_extract": extract_for(best["page"]) if best and best["page"]["status"] == "ok" else "",
                           "other_urls": " | ".join(c["url"] for c in cands[1:])})
            if a.eval:
                stats["eval_in_review_seed_host_among_candidates" if any(host_of(c["url"]) == host_of(seed_site.get(pin["venue_id"], "x")) for c in cands) else "eval_seed_site_never_found"] += 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tag = "_eval" if a.eval else ""
    with (OUT_DIR / f"proposed_rows{tag}.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=SEED_FIELDS, lineterminator="\r\n")
        w.writeheader()
        w.writerows(proposed)
    with (OUT_DIR / f"review_queue{tag}.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=REVIEW_FIELDS)
        w.writeheader()
        w.writerows(review)
    n = len(pins)
    lines = [f"# Website finder report {today}{' (eval vs seed)' if a.eval else ''}", "",
             f"- pins checked: {n}", f"- resolved by script (auto rows): {stats['auto']} ({100 * stats['auto'] // max(n, 1)}%)",
             f"- left for a model: {n - stats['auto']} (candidate found but a check failed: {stats['review_with_candidate']}; "
             f"pages fetched, none matched: {stats['no_page_passed']}; no candidate url: {stats['no_candidate']})"]
    if a.eval:
        lines += [f"- eval: auto rows on the same host as the past pass: {stats['eval_auto_same_host_as_seed']}, different: {stats['eval_auto_DIFFERENT_from_seed']}",
                  f"- eval: sent to review but the past pass's site was among the candidates: {stats['eval_in_review_seed_host_among_candidates']}; never found: {stats['eval_seed_site_never_found']}"]
    (OUT_DIR / f"report{tag}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"files in {OUT_DIR}")
    if a.apply and not a.eval:
        print(f"appended {append_seed(proposed)} rows to {SEED.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
