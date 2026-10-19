"""Seed official tennis court counts from two city one-page directories: SF Rec & Park and the City of San Diego.

    python ingestion/city_tennis_directories.py                 # report: parse, geocode (cached), match to mapped tennis pins
    python ingestion/city_tennis_directories.py --emit rows.csv # also write manual_venues.csv rows to append

SF  https://sfrecpark.org/1446/Tennis-Court-Directory   facility, ZIP, lights, restrooms, total / reservable / walk-up courts (no address)
SD  https://www.sandiego.gov/park-and-recreation/activities/sports/tenniscourts   facility, address, court count, lights, hours

Both pages answer plain HTTP (no browser needed). Locations: each facility is geocoded once with Nominatim (1 request/s, project User-Agent,
cached in ingestion/data/city_tennis_geocode.csv). A facility is linked to the nearest mapped Tennis pin within --radius-m of that point; the
seed row then carries the pin's own coordinates (int_manual_venue_match merges it). No pin in range -> a new pin at the geocoded point,
flagged approximate. Note bridge_venue_sport takes max(OSM courts, manual courts), so an official count cannot lower an inflated OSM count.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import math
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = "courtconnect-ca/0.1 (+https://github.com/abov/courtconnect-ca)"
SF_URL = "https://sfrecpark.org/1446/Tennis-Court-Directory"
SF_RULES = "https://sfrecpark.org/1887/Walk-Up-Tennis-Court-Rules"
SF_BOOK = "https://sfrecpark.org/1188/How-to-Book-a-Tennis-or-Pickleball-Court"
SD_URL = "https://www.sandiego.gov/park-and-recreation/activities/sports/tenniscourts"
CACHE = ROOT / "ingestion/data/city_tennis_geocode.csv"
BOX = {"San Francisco": (37.70, 37.83, -122.52, -122.36), "San Diego": (32.55, 33.05, -117.30, -116.90)}
NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}
HEADER = ["venue_key", "venue_name", "sport", "city", "lat", "lon", "location_precision", "website", "surface_type", "setting", "offerings",
          "courts", "access", "rules", "confirmation", "confirmed_on", "evidence", "region"]


def page_text(url: str) -> str:
    raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30).read()
    try:
        h = raw.decode("utf-8")
    except UnicodeDecodeError:
        h = raw.decode("cp1252")
    h = re.sub(r"(?is)<(script|style|nav|header|footer)[^>]*>.*?</\1>", "", h)
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)))


def sf_rows():
    t = page_text(SF_URL)
    out = []
    for nm, zp, lit, rest, tot, res, wu in re.findall(r"([A-Z][A-Za-z0-9.&'’() ]+?) (9\d{4}) (Yes|No) (Yes|No) (\d+) (\d+) (\d+)", t):
        out.append({"city": "San Francisco", "name": nm.strip(), "zip": zp, "lit": lit == "Yes", "courts": int(tot), "reservable": int(res), "walkup": int(wu)})
    return out


def sd_rows():
    t = page_text(SD_URL)
    pat = re.compile(r"([A-Z][^0-9]+?) \1 ([^,]+?, 9\d{4}) [\d-]+ (\w+) courts? - (lighted|no lights) ")
    ms = list(pat.finditer(t))
    end = t.find("Recreation Centers and Pools Employment")
    out = []
    for i, m in enumerate(ms):
        stop = ms[i + 1].start() if i + 1 < len(ms) else end
        n = NUM.get(m.group(3).lower(), int(m.group(3)) if m.group(3).isdigit() else None)
        out.append({"city": "San Diego", "name": m.group(1).strip(), "addr": m.group(2).strip(), "courts": n, "lit": m.group(4) == "lighted",
                    "hours": t[m.end():stop].strip()})
    return out


def load_cache():
    out: dict = {}
    if CACHE.exists():
        for r in csv.DictReader(open(CACHE, encoding="utf-8")):
            out.setdefault(r["query"], [])
            if r["lat"]:
                out[r["query"]].append((float(r["lat"]), float(r["lon"]), r["display"]))
    return out


def nominatim(q: str, cache: dict):
    """Up to 5 Nominatim results for a query (cached, so a rerun makes no requests)."""
    if q not in cache:
        url = "https://nominatim.openstreetmap.org/search?format=jsonv2&limit=5&q=" + urllib.parse.quote(q)
        for wait in (0, 60, 180, 300):   # 429 = rate limited: back off, never hammer
            time.sleep(wait + 1.1)
            try:
                r = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30))
                break
            except urllib.error.HTTPError as e:
                if e.code not in (429, 502, 503, 504):
                    raise
            except (urllib.error.URLError, TimeoutError):
                pass   # connection dropped or timed out: back off and retry
        else:
            save_cache(cache)
            raise SystemExit("Nominatim keeps answering 429: stop, wait, rerun (the cache keeps what was fetched)")
        cache[q] = [(float(x["lat"]), float(x["lon"]), x["display_name"][:120]) for x in r]
        save_cache(cache)
    return cache[q]


def save_cache(cache):
    with open(CACHE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["query", "lat", "lon", "display"])
        for q, vs in sorted(cache.items()):
            for v in vs or [("", "", "")]:
                w.writerow([q, *v])


def candidates(row, cache):
    """Candidate points for a facility: results of address / name queries that fall inside the city box."""
    box = BOX[row["city"]]
    qs = [row["addr"] + ", San Diego, CA"] if "addr" in row else []
    n, c = row["name"], row["city"]
    qs += [f"{n} Tennis Courts, {c}, California", f"{n} Park, {c}, California", f"{n} Playground, {c}, California", f"{n} Recreation Center, {c}, California", f"{n}, {c}, California"]
    seen = set()
    for q in qs:   # lazy: the caller stops at the first point that lands on a fitting mapped pin, so most facilities cost one request
        for lat, lon, disp in nominatim(q, cache):
            if box[0] <= lat <= box[1] and box[2] <= lon <= box[3] and (lat, lon) not in seen:
                seen.add((lat, lon))
                yield lat, lon, q


PIN_HINTS = {"Mission": "Mission Playground"}   # directory name -> mapped pin it is, checked by hand (the geocode lands on Dolores Park)
GENERIC = {"park", "playground", "rec", "recreation", "center", "community", "courts", "court", "tennis", "square", "and", "the", "club", "sports", "complex", "field", "athletic", "st", "street"}


def toks(s):
    return {w for w in re.sub(r"[^a-z0-9 ]", " ", s.lower()).split() if w not in GENERIC}


def name_ok(dir_name, pin_name):
    # an unnamed / generic pin ('Tennis Courts') may be anything; a named pin must share a significant word with the directory name
    return not pin_name or not toks(pin_name) or bool(toks(dir_name) & toks(pin_name))


def metres(a, b, c, d):
    return math.hypot((c - a) * 111_320, (d - b) * 111_320 * math.cos(math.radians((a + c) / 2)))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--radius-m", type=float, default=250)
    ap.add_argument("--emit")
    args = ap.parse_args()
    app = json.load(open(ROOT / "app/data/venues.json", encoding="utf-8"))
    ti = [s["n"] for s in app["sports"]].index("Tennis")
    pins = [(v["y"], v["x"], v["n"], dict((p[0], p[1]) for p in v["p"])[ti]) for v in app["venues"] if any(p[0] == ti for p in v["p"])]
    seeds = list(csv.DictReader(open(ROOT / "transform/seeds/manual_venues.csv", encoding="utf-8")))
    cache = load_cache()
    rows, out = sf_rows() + sd_rows(), []
    stats ={"linked": 0, "new": 0, "review": 0}
    for r in rows:
        cands, best = [], None   # best = (score, distance, pin, point): the candidate point nearest a mapped pin that fits (same count, or a name that overlaps)
        for lat, lon, how in candidates(r, cache):
            cands.append((lat, lon, how))
            for y, x, n, c in pins:
                d = metres(lat, lon, y, x)
                hint = PIN_HINTS.get(r["name"])
                if hint:   # checked by hand: the directory's park is this named pin
                    ok = hint.lower() in n.lower() and d <= 800
                else:
                    overlap = bool(toks(r["name"]) & toks(n))
                    ok = (overlap and d <= 600) or (not toks(n) and d <= args.radius_m) or (c == r["courts"] and d <= args.radius_m)
                if ok:
                    fit = (0 if hint or toks(r["name"]) & toks(n) else 1, d)
                    if best is None or fit < best[0]:
                        best = (fit, d, (y, x, n, c), (lat, lon, how))
            if best and best[1] <= 150:   # a close fit ends the search; a loose one may be beaten by the next candidate point
                break
        slug = re.sub(r"[^a-z0-9]+", "-", r["name"].lower()).strip("-")
        r["key"] = ("sf-rec-" if r["city"] == "San Francisco" else "sd-city-") + slug + "-tennis"
        r["pin"], r["review"] = None, ""
        if best:
            _, d, pin, (lat, lon, how) = best
            r.update(pin=pin + (round(d),), lat=pin[0], lon=pin[1])
            r["prec"] = f"existing map pin{' ' + repr(pin[2]) if pin[2] else ''} ({round(d)} m from the directory's park; park found by '{how}'); the courts' exact spot in the park is the mapped one"
            stats["linked"] += 1
        elif cands:
            lat, lon, how = cands[0]
            clash = sorted((round(metres(lat, lon, y, x)), n, c) for y, x, n, c in pins if metres(lat, lon, y, x) <= 400)
            r.update(lat=round(lat, 6), lon=round(lon, 6))
            r["prec"] = f"approximate: Nominatim point for '{how}'; no mapped tennis pin fits within {args.radius_m:.0f} m, so the courts' exact spot is not pinned"
            if clash:
                r["review"] = f"a mapped tennis pin sits within 400 m (a new pin could duplicate it, or the 150 m merge would absorb it): {clash[:2]}"
            stats["review" if clash else "new"] += 1
        else:
            r["review"] = "no geocode"; r["lat"] = r["lon"] = None; r["prec"] = ""; stats["review"] += 1
        r["dup"] = [s["venue_key"] for s in seeds if r["lat"] and s["sport"] == "Tennis" and metres(r["lat"], r["lon"], float(s["lat"]), float(s["lon"])) <= 150 and s["venue_key"] != r["key"]]
        flag = "" if r["pin"] is None or r["pin"][3] == r["courts"] else f"  [map has {r['pin'][3]}]"
        status = ("pin %3d m %-26s" % (r["pin"][4], repr(r["pin"][2])[:26])) if r["pin"] else ("REVIEW" if r["review"] else "NEW PIN")
        print(f"{r['city'][:3]} {r['name'][:36]:36} {r['courts']:>3}  {status}{flag}{'  [existing seed ' + r['dup'][0] + ']' if r['dup'] else ''}{'  ' + r['review'] if r['review'] else ''}")
        out.append(r)
    save_cache(cache)
    print(stats, "rows", len(rows))
    if args.emit:
        emit(out, args.emit)


def emit(rows, path):
    d = "2026-10-18"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HEADER, lineterminator="\r\n")
        for r in rows:
            if r["dup"] or r["review"]:
                continue
            nm = r["pin"][2] if r["pin"] and r["pin"][2] else r["name"] + " tennis courts"
            if r["city"] == "San Francisco":
                rules = (f"SF Rec & Park: {r['reservable']} reservable court(s) ($5 per court-hour, book at rec.us/sfrecpark: {SF_BOOK}), "
                         f"{r['walkup']} walk-up court(s) (first come, first served; rules: {SF_RULES}). Lights: {'yes' if r['lit'] else 'no'}.")
                ev = (f"SF Recreation and Park Department Tennis Court Directory ({SF_URL}), read {d}: {r['name']} (ZIP {r['zip']}), {r['courts']} courts, "
                      f"{r['reservable']} reservable, {r['walkup']} walk-up, lights {'yes' if r['lit'] else 'no'}. Location: {r['prec']}. Found by ingestion/city_tennis_directories.py.")
                site = SF_URL
            else:
                rules = f"City of San Diego listing hours: {r['hours']}. {r['courts']} court(s), {'lighted' if r['lit'] else 'no lights'}. The page gives no fees or reservation rules."
                ev = (f"City of San Diego Parks & Recreation 'Tennis Courts' page ({SD_URL}), read {d}: {r['name']}, {r['addr']}, {r['courts']} courts, "
                      f"{'lighted' if r['lit'] else 'no lights'}, hours {r['hours']}. Location: {r['prec']}. Found by ingestion/city_tennis_directories.py.")
                site = SD_URL
            w.writerow({"venue_key": r["key"], "venue_name": nm, "sport": "Tennis", "city": r["city"], "lat": f"{r['lat']:.6f}", "lon": f"{r['lon']:.6f}",
                        "location_precision": r["prec"], "website": site, "surface_type": "unknown", "setting": "unknown", "offerings": "", "courts": r["courts"],
                        "access": "public", "rules": rules, "confirmation": "official", "confirmed_on": d, "evidence": ev, "region": "CA"})


if __name__ == "__main__":
    main()
