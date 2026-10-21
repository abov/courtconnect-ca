"""Scan public 24 Hour Fitness club pages (URLs from their sitemap) for CA/NV clubs that list a racquetball court.
Usage: .venv/Scripts/python.exe -I ingestion/oneoff/scan_24hour.py out.csv   (writes url,name,street,city,state,zip,phone,lat,lon,racquetball,squash; ~3 min, throttled)."""
import csv, html, json, re, sys, time, urllib.request

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # shared helpers in ingestion/
from useragent import HEADERS as UA
get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read().decode("utf-8", "ignore")
urls = sorted(set(re.findall(r"<loc>(https://www\.24hourfitness\.com/gyms/[a-z0-9-]+-(?:ca|nv)/[a-z0-9-]+)</loc>", get("https://www.24hourfitness.com/sitemap.xml"))))
w = csv.writer(open(sys.argv[1], "w", newline="", encoding="utf-8"))
w.writerow(["url", "name", "street", "city", "state", "zip", "phone", "lat", "lon", "racquetball", "squash"])
for u in urls:
    try:
        t = get(u)
    except Exception:
        continue
    g = lambda k: (re.search(r'"%s":\s*"([^"]*)"' % k, t) or [None, ""])[1]
    lat = re.search(r'"latitude":\s*(-?[\d.]+)', t); lon = re.search(r'"longitude":\s*(-?[\d.]+)', t)
    title = re.search(r"<title>\s*([^<|]*)", t)
    w.writerow([u, html.unescape(title.group(1)).strip() if title else "", html.unescape(g("streetAddress")), g("addressLocality"), g("addressRegion"), g("postalCode"), g("telephone"),
                lat.group(1) if lat else "", lon.group(1) if lon else "", int(bool(re.search(r"Racquetball Court", t))), int(bool(re.search(r"Squash Court", t)))])
    time.sleep(0.5)
