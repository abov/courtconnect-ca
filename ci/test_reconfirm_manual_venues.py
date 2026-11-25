"""Offline test for ingestion/reconfirm_manual_venues.py: only rows whose page still names the place and sport are re-dated,
everything else (403, missing name, missing sport) is queued, and untouched seed lines stay byte-for-byte (a quoted field may span lines)."""
import csv
import os
import sys
import tempfile
sys.path.insert(0, "ingestion")
import reconfirm_manual_venues as m

t = m.page_text("<title>Parque Frontón</title><p>Manhattan Heights Park: pickleball &amp; tennis</p>".encode())
assert m.name_on_page("Manhattan Heights Park", t) and m.sport_on_page("Pickleball", t)
assert not m.sport_on_page("Padel", t) and not m.name_on_page("Polliwog Park", t)
assert not m.name_on_page("Tennis Courts", t)            # only generic words: the whole name must be on the page
assert m.name_on_page("Parque Fronton (our note)", t)     # accents folded, our bracketed notes ignored

seed = ("venue_key,venue_name,sport,website,confirmed_on,evidence\n"
        "a,Alpha Park,Tennis,https://x.test/a,2026-01-01,read once\n"
        'b,Beta Club,Padel,https://x.test/b,2026-01-01,"two\nlines"\n'
        "c,Gamma Gym,Squash,https://x.test/c,,\n"
        "d,Delta Courts,Pickleball,,2026-01-01,no site\n")
pages = {"https://x.test/a": ("ok", m.page_text(b"Alpha Park tennis")), "https://x.test/b": ("ok", m.page_text(b"Beta Club tennis")),
         "https://x.test/c": ("http 403", "")}
with tempfile.TemporaryDirectory() as d:
    m.SEED, m.PAUSE = os.path.join(d, "seed.csv"), 0
    open(m.SEED, "w", encoding="utf-8", newline="").write(seed)
    m.fetch = pages.get
    sys.argv = ["x", "--queue", os.path.join(d, "q.csv")]
    m.main()
    out = open(m.SEED, encoding="utf-8", newline="").read()
    rows = {r["venue_key"]: r for r in csv.DictReader(open(m.SEED, encoding="utf-8", newline=""))}
    queue = {r["venue_key"]: r["reason"] for r in csv.DictReader(open(os.path.join(d, "q.csv"), encoding="utf-8"))}
assert rows["a"]["confirmed_on"] != "2026-01-01" and "still names the place and Tennis" in rows["a"]["evidence"]
assert out.split("\n", 2)[2:] and 'b,Beta Club,Padel,https://x.test/b,2026-01-01,"two\nlines"\n' in out   # untouched, multi-line kept
assert rows["c"]["confirmed_on"] == "" and rows["d"]["confirmed_on"] == "2026-01-01"
assert queue == {"b": "page names the place but not Padel", "c": "http 403"}, queue
print("reconfirm_manual_venues: ok")
