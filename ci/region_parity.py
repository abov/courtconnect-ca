"""Parity audit: what each covered state has, item type by item type, so a new state is never "done" with silent zeros (ADR 0028 parity rule).

Read-only; reads ingestion/regions.json, the seeds, app/data/*.json and the shared raw CSVs. Events and social rows have no region column, so they are
placed through the border polygon (data/raw/*_border.wkt, fetched on first use); venues use the exported region code.

Run: python ci/region_parity.py                 (matrix for every region, zeros marked)
     python ci/region_parity.py --region AZ     (one region, with the "state is done" verdict)
     python ci/region_parity.py --region AZ --strict   (exit 1 if a required item is zero; use before calling a state done)
A required zero that was searched and found empty goes in ci/parity_logged_empty.csv (region, item, evidence, verified_on) and no longer fails --strict.
Checklist and recipe: docs/new_region_checklist.md
"""
import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ingestion"))
import overpass  # noqa: E402
import rawdir  # noqa: E402

REGIONS = json.loads((ROOT / "ingestion" / "regions.json").read_text(encoding="utf-8"))["regions"]
SEEDS = ROOT / "transform" / "seeds"
APP = ROOT / "app"

# Sports every state's pass must at least have searched; a zero is a gap to name (or to log as "searched, empty" in docs/event_group_search.md).
SPORTS = ["Pickleball", "Padel", "Pop Tennis", "Beach Tennis", "Squash", "Table Tennis", "Badminton", "Racquetball"]
# Wall types in the export (`hw.t`): 1-wall and 3-wall handball/wallball courts and backboards, each searched for in every state.
WALL_KINDS = ["one_wall", "three_wall", "backboard"]
# Docs that need a section per state (case-insensitive substring of the state's `name` in regions.json).
DOCS = ["docs/event_group_search.md", "docs/public_facility_scan.md", "docs/padel_scan.md", "docs/gym_chain_scan.md"]
# Items that may not be zero before a state is called done (everything else is shown but only reported).
REQUIRED = ["pins", "manual venues", "hitting walls (export)", "one_wall wall pins", "three_wall wall pins", "backboard wall pins", "handball wall pins",
            "hitting walls (OSM)", "walls (hand-added)", "watch events", "social series", "link-outs (hand-added)",
            "street addresses", "zip codes", "places", "outline", "home view fits", "doc sections"]


def logged_empty():
    """{region: {item}} from ci/parity_logged_empty.csv: required items that were searched and are empty, each with its evidence and date. A row without both does not count."""
    path = ROOT / "ci" / "parity_logged_empty.csv"
    out = {}
    if path.exists():
        with open(path, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                if r["evidence"].strip() and r["verified_on"].strip():
                    out.setdefault(r["region"].upper(), set()).add(r["item"])
    return out


def region_of(lat, lon):
    return overpass.region_at(lat, lon)   # border polygon (cached WKT), so Las Vegas is NV although it sits inside California's box


def seed(name):
    with open(SEEDS / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def by_coord(rows, lat="lat", lon="lon"):
    c = Counter()
    for r in rows:
        try:
            c[region_of(float(r[lat]), float(r[lon]))] += 1
        except (KeyError, ValueError):
            c["?"] += 1
    return c


def home_view_fits(cfg, margin=0.25):
    """1 if the region's box sits inside app/index.html HOME_BOUNDS with `margin` degrees to spare (a line on the screen edge is hidden by the UI; Arizona's was). Regions far outside it (Hawaii) have their own shortcut: counted as fine. A region with `home_shortcut` in regions.json (the id of its control in index.html, the Country dropdown for Mexico) fits if that control exists."""
    west, south, east, north = map(float, re.search(r"HOME_BOUNDS = \[\[(.+?), (.+?)\], \[(.+?), (.+?)\]\]", (APP / "index.html").read_text(encoding="utf-8")).groups())
    s, w, n, e = cfg["bbox"]
    if cfg.get("home_shortcut"):   # a region the home view frames only in part (Mexico, ADR 0034: the home view covers the pilot and the pins, the rest of the country is the Country dropdown) must have its own control in the page
        return int(f'id="{cfg["home_shortcut"]}"' in (APP / "index.html").read_text(encoding="utf-8"))
    if e < west - 5 or w > east + 5 or n < south - 5 or s > north + 5:
        return 1
    return int(w - west >= margin and s - south >= margin and east - e >= margin and north - n >= margin)


def audit():
    export = json.loads((APP / "data" / "venues.json").read_text(encoding="utf-8"))
    sport_idx = {s["n"]: i for i, s in enumerate(export["sports"])}
    m = {code: {} for code in REGIONS}
    pins = Counter(v["r"] for v in export["venues"])
    street = Counter(v["r"] for v in export["venues"] if v.get("ns"))
    confirmed = Counter(v["r"] for v in export["venues"] if v["q"] == "c")
    hw = Counter(v["r"] for v in export["venues"] if v.get("hw") is not None)
    wall_pins = [v for v in export["venues"] if isinstance(v.get("hw"), dict)]
    wall_kind = {k: Counter(v["r"] for v in wall_pins if k in v["hw"].get("t", [])) for k in WALL_KINDS}
    handball = Counter(v["r"] for v in wall_pins if "Handball" in v["hw"].get("sp", []))
    per_sport = {sp: Counter(v["r"] for v in export["venues"] if any(p[0] == sport_idx.get(sp) for p in v["p"])) for sp in SPORTS}

    manual = seed("manual_venues.csv")
    manual_region = {r["venue_key"]: r["region"] for r in manual}
    manual_n = Counter(r["region"] for r in manual)
    walls_manual = Counter(r["region"] for r in seed("manual_walls.csv"))
    walls_osm = Counter()
    walls_file = rawdir.raw_dir() / "osm_walls.csv"
    if walls_file.exists():
        with open(walls_file, encoding="utf-8", newline="") as f:
            walls_osm = Counter(r["region"] for r in csv.DictReader(f))
    events = by_coord(seed("watch_events.csv"))
    social = by_coord(seed("social_events.csv"))
    linkouts = Counter(manual_region.get(r["venue_ref"]) for r in seed("venue_actions.csv") if r["venue_ref_type"] == "manual")
    zips = Counter(region_of(*ll) for ll in json.loads((APP / "data" / "zips.json").read_text(encoding="utf-8")).values())
    places = Counter(p[1] for p in json.loads((APP / "data" / "places.json").read_text(encoding="utf-8")))
    outline = {f["properties"]["name"].lower() for f in json.loads((APP / "data" / "state_outline.json").read_text(encoding="utf-8"))["features"]}
    docs_text = {d: (ROOT / d).read_text(encoding="utf-8").lower() for d in DOCS if (ROOT / d).exists()}

    for code, cfg in REGIONS.items():
        r = m[code]
        r["pins"] = pins[code]
        r["confirmed pins"] = confirmed[code]
        r["street addresses"] = street[code]
        r["manual venues"] = manual_n[code]
        r["hitting walls (export)"] = hw[code]
        for k in WALL_KINDS:
            r[f"{k} wall pins"] = wall_kind[k][code]
        r["handball wall pins"] = handball[code]
        r["hitting walls (OSM)"] = walls_osm[code]
        r["walls (hand-added)"] = walls_manual[code]
        r["watch events"] = events[code]
        r["social series"] = social[code]
        r["link-outs (hand-added)"] = linkouts[code]
        r["zip codes"] = zips[code]
        r["places"] = places[code]
        r["outline"] = int(cfg["name"] in outline)
        r["home view fits"] = home_view_fits(cfg)
        r["doc sections"] = sum(cfg["name"] in t for t in docs_text.values())
        for sp in SPORTS:
            r[f"{sp} pins"] = per_sport[sp][code]
    return m


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--region")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    m = audit()
    codes = [a.region.upper()] if a.region else list(m)
    items = list(next(iter(m.values())))
    w = max(len(i) for i in items)
    print(f"{'':{w}}  " + "  ".join(f"{c:>7}" for c in codes))
    empty_ok = logged_empty()
    for item in items:
        note = "   <- required" if item in REQUIRED else ""
        if any(m[c][item] == 0 and item in empty_ok.get(c, ()) for c in codes):
            note += " (logged empty)"
        print(f"{item:{w}}  " + "  ".join(f"{m[c][item]:>7}" for c in codes) + note)
    bad = {c: [i for i in items if m[c][i] == 0 and i in REQUIRED and i not in empty_ok.get(c, ())] for c in codes}
    for c in codes:
        zero_sports = [s for s in SPORTS if m[c][f"{s} pins"] == 0]
        print(f"\n{c}: required items at zero: {bad[c] or 'none'}")
        print(f"{c}: sports with no pins (searched and empty, or a gap?): {zero_sports or 'none'}")
    print("\nNot counted here (check by hand, docs/new_region_checklist.md): player_groups, leads, routine source lists, app strings, ask.py, llms.txt, CI fixtures.")
    if a.strict and any(bad.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
