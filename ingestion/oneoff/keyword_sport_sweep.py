"""Keyword sweep: OSM venues tagged or named for a racket sport that RacketConnect does not list yet.

Queries Overpass per region (MX plus the US regions in regions.json) for sport= values, name~ and description~ keywords
(English plus Spanish) of every sport in transform/seeds/all_racquet.csv, matches each hit to a sport, then keeps only hits
with no pin for that sport within --radius metres in app/data/venues.json (read by script, never opened whole).
Tennis, table tennis and pickleball are searched by name only (their sport= tags are already extracted statewide).

    python ingestion/oneoff/keyword_sport_sweep.py query --region MX --out <dir>     # slow, resumable: caches raw hits per region
    python ingestion/oneoff/keyword_sport_sweep.py diff --out <dir> [--region MX]    # candidates not yet pinned for that sport

Output goes to <dir> (raw_<region>.json, candidates.csv), outside the repo. Public OSM data only (ADR 0005).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import overpass  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
VENUES = ROOT / "app" / "data" / "venues.json"
SPORTS_CSV = ROOT / "transform" / "seeds" / "all_racquet.csv"

# sport -> (sport= values, extra name/description keywords). The sport's own name is always a keyword too.
SPEC: dict[str, tuple[list[str], list[str]]] = {
    "Badminton": (["badminton", "badmington"], ["bádminton", "bádmington", "plumilla", "bulu tangkis"]),
    "Squash": (["squash"], ["squash"]),
    "Racquetball": (["racquetball", "racketball"], ["raquetbol", "raquetball", "racquet ball", "raquetbol"]),
    "Outdoor Racquetball": (["outdoor_racquetball"], ["outdoor racquetball"]),
    "Padel": (["padel", "paddle"], ["pádel", "padel", "paddle tennis"]),
    "Pickleball": ([], ["pickle ball", "picklebol", "pickle-ball"]),
    "Pop Tennis": (["paddle_tennis", "paddletennis", "pop_tennis", "poptennis"], ["paddle tennis", "pop tenis"]),
    "Platform Tennis": (["platform_tennis"], ["platform tennis", "paddle tennis"]),
    "Beach Tennis": (["beach_tennis", "beachtennis"], ["tenis de playa", "tenis playa", "beach tenis"]),
    "Table Tennis": ([], ["ping pong", "ping-pong", "pingpong", "tenis de mesa", "tennis de table"]),
    "Real Tennis": (["real_tennis"], ["real tennis", "royal tennis", "court tennis"]),
    "Tennis": ([], ["tenis"]),
    "4-wall Paddleball": (["paddleball"], ["paddleball", "four-wall", "4 wall"]),
    "1-wall Paddleball": ([], ["one-wall", "1-wall", "1 wall"]),
    "3-wall Paddleball": ([], ["three-wall", "3-wall", "3 wall"]),
    "Basque Pelota: Frontenis": (["frontenis", "pelota", "fronton", "basque_pelota", "pelota_vasca", "jai_alai"],
                                 ["frontón", "frontenis", "fronton", "pelota vasca", "pelota", "paleta", "pala corta", "trinquete",
                                  "cesta punta", "jai-alai", "frontón", "rebote"]),
    "Basque Pelota: Jai Alai": (["jai_alai", "cesta_punta"], ["jai alai", "jai-alai", "cesta punta"]),
    "Hand Tennis": (["jeu_de_paume"], ["hand tennis", "jeu de paume"]),
    "Soft Tennis": (["soft_tennis"], ["soft tennis", "soft-tennis", "tenis blando"]),
    "Crossminton": (["crossminton", "speedminton"], ["speedminton", "speed badminton"]),
    "Touchtennis": (["touchtennis"], ["touch tennis"]),
    "Totem Tennis": (["swingball"], ["swingball", "totem tennis"]),
    "Tamburello": (["tamburello"], ["tamburrello"]),
    "Frescoball": ([], ["frescobol", "frescobol"]),
    "Smashball": ([], ["matkot", "smash ball"]),
    "Jokari": (["jokari"], ["jokari"]),
    "Tenis criollo": ([], ["tenis criollo"]),
    "Floor Pro Mini Tennis": ([], ["mini tennis", "mini tenis", "miniten", "mini-tennis"]),
    "Tennis Baseball": (["tennis_baseball"], ["tenis beisbol"]),
}
# sport= values that map straight to a sport with no name keyword needed
EXTRA_SPORT_VALUES = {"fives": "Real Tennis", "eton_fives": "Real Tennis", "rugby_fives": "Real Tennis", "rackets": "Real Tennis",
                      "racketlon": "Badminton", "ping_pong": "Table Tennis"}
SKIP_SPORT_VALUES = {"tennis", "table_tennis", "tennis_table", "pickleball"}  # extracted statewide already: name search only
NAME_ONLY_REGIONS = {"Tennis": {"MX"}}  # tenis in a name: only worth the load in Mexico
NOISY = {"Speedball", "Ricochet", "Skyball", "Naked Tennis", "Street Racket", "Racket Hockey", "Toccer", "Smolball"}

REGIONS = ["MX", "CA", "NV", "OR", "WA", "HI", "AZ", "NM", "TX"]


def sports() -> list[str]:
    with SPORTS_CSV.open(newline="", encoding="utf-8") as f:
        return [r["sport"] for r in csv.DictReader(f)]


def keywords() -> dict[str, list[str]]:
    """sport -> lower-case keywords (name, description). Sports in SPEC add their own; every other sport uses its name."""
    out: dict[str, list[str]] = {}
    for s in sports():
        if s.startswith("Basque Pelota") and s not in SPEC:
            continue
        kw = {s.lower().split(": ")[-1]} | {k.lower() for k in SPEC.get(s, ([], []))[1]}
        if s in ("Tennis", "Table Tennis"):
            kw.discard(s.lower())
        out[s] = sorted(kw)
    for s in SPEC:
        out.setdefault(s, sorted({k.lower() for k in SPEC[s][1]} | ({s.lower()} if s not in ("Tennis", "Table Tennis") else set())))
    return out


TAG_ONLY = {"pickleball": "Pickleball", "table_tennis": "Table Tennis", "tennis_table": "Table Tennis"}  # --tags-only mode


def sport_value_map(tags_only: bool = False) -> dict[str, str]:
    if tags_only:
        return dict(TAG_ONLY)
    m = dict(EXTRA_SPORT_VALUES)
    for s, (vals, _) in SPEC.items():
        for v in vals:
            m.setdefault(v, s)
    return {k: v for k, v in m.items() if k not in SKIP_SPORT_VALUES}


def esc(s: str) -> str:
    return re.sub(r"([.\\+*?\[^\]$(){}=!<>|:\-])", r"\\\1", s)


def build_query_for(region: str, tags_only: bool = False):
    if tags_only:
        sv = "|".join(sorted(TAG_ONLY))
        return lambda bbox: f"""
        {overpass.header(bbox)}
        nwr["sport"~"(^|;)({sv})($|;)"];
        out center tags;
        """
    kws = keywords()
    words = sorted({w for s, ws in kws.items() for w in ws if region in NAME_ONLY_REGIONS.get(s, REGIONS)})
    name_rx = "|".join(esc(w) for w in words)
    sv = "|".join(sorted(sport_value_map()))

    def build(bbox):
        return f"""
        {overpass.header(bbox)}
        (
          nwr["sport"~"(^|;)({sv})($|;)"];
          nwr["name"~"{name_rx}",i];
          nwr["description"~"{name_rx}",i];
        );
        out center tags;
        """
    return build


def tiles_for(region: str):
    return overpass.tiles(region, 3.2, 4.2)


def cmd_query(args) -> None:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for region in args.region or REGIONS:
        path = out / f"raw_{region}{'_tags' if args.tags_only else ''}.json"
        done = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"tiles": {}, "failed": []}
        build = build_query_for(region, args.tags_only)
        tl = tiles_for(region)
        failed: list = []
        for i, bbox in enumerate(tl, 1):
            key = str(list(bbox))
            if key in done["tiles"]:
                continue
            els = overpass.fetch_adaptive(build, bbox, f"{region} {i}/{len(tl)}", failed)
            done["tiles"][key] = [e for e in els if e.get("tags")]
            done["failed"] = [list(b) for b in failed]
            path.write_text(json.dumps(done, ensure_ascii=False), encoding="utf-8")
            print(f"{region} tile {i}/{len(tl)} {bbox}: {len(els):,} elements", flush=True)
            time.sleep(2)
        print(f"{region}: failed tiles {failed}" if failed else f"{region}: all tiles ok", flush=True)


def match_sports(tags: dict, region: str, kws: dict[str, list[str]], svm: dict[str, str]) -> dict[str, str]:
    """sport -> how it matched ('sport=', 'name', 'description')."""
    hit: dict[str, str] = {}
    for v in re.split(r"[;,]", (tags.get("sport") or "").lower()):
        if v.strip() in svm:
            hit[svm[v.strip()]] = "sport="
    for field in ("name", "description"):
        text = (tags.get(field) or "").lower()
        if not text:
            continue
        for s, ws in kws.items():
            if region not in NAME_ONLY_REGIONS.get(s, REGIONS) or s in hit:
                continue
            if any(re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", text) for w in ws):   # whole words: "ketball" is not "basketball"
                hit[s] = field
    return hit


def metres(lat1, lon1, lat2, lon2) -> float:
    return math.hypot((lat2 - lat1) * 111_320, (lon2 - lon1) * 111_320 * math.cos(math.radians((lat1 + lat2) / 2)))


def cmd_diff(args) -> None:
    d = json.loads(VENUES.read_text(encoding="utf-8"))
    names = [s["n"] for s in d["sports"]]
    grid: dict[tuple, list[tuple]] = {}
    for v in d["venues"]:
        grid.setdefault((round(v["y"], 2), round(v["x"], 2)), []).append((v["y"], v["x"], {names[p[0]] for p in v["p"]}, v["n"], v["i"]))

    def near(lat, lon):
        out = []
        for dy in (-0.01, 0, 0.01):
            for dx in (-0.01, 0, 0.01):
                for y, x, sp, n, i in grid.get((round(lat + dy, 2), round(lon + dx, 2)), []):
                    out.append((metres(lat, lon, y, x), sp, n, i))
        return sorted(out)

    kws, svm = ({}, sport_value_map(True)) if args.tags_only else (keywords(), sport_value_map())
    rows, seen = [], set()
    for region in args.region or REGIONS:
        path = Path(args.out) / f"raw_{region}{'_tags' if args.tags_only else ''}.json"
        if not path.exists():
            continue
        raw = json.loads(path.read_text(encoding="utf-8"))
        for els in raw["tiles"].values():
            for e in els:
                key = (e["type"], e["id"])
                if key in seen:
                    continue
                seen.add(key)
                c = e.get("center", {})
                lat, lon = e.get("lat", c.get("lat")), e.get("lon", c.get("lon"))
                if lat is None or overpass.region_at(lat, lon) != region:
                    continue
                t = e["tags"]
                hit = match_sports(t, region, kws, svm)
                if not hit:
                    continue
                nb = near(lat, lon)
                for s, how in hit.items():
                    if any(dist <= args.radius and s in sp for dist, sp, _, _ in nb):
                        continue
                    first = nb[0] if nb else None
                    rows.append({"region": region, "sport": s, "how": how, "osm": f"{e['type']}/{e['id']}", "lat": round(lat, 5), "lon": round(lon, 5),
                                 "name": t.get("name", ""), "sport_tag": t.get("sport", ""), "kind": t.get("leisure") or t.get("amenity") or t.get("shop") or t.get("tourism") or "",
                                 "desc": (t.get("description") or "")[:100], "city": t.get("addr:city", ""),
                                 "nearest_m": round(first[0]) if first else "", "nearest_name": first[2] if first else "", "noisy": int(s in NOISY)})
    rows.sort(key=lambda r: (r["region"], r["sport"], r["how"] != "sport=", r["name"] == ""))
    out = Path(args.out) / ("candidates_tags.csv" if args.tags_only else "candidates.csv")
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["region"])
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    print(f"{len(rows)} candidates -> {out}")
    for (r, s, h), n in sorted(Counter((r["region"], r["sport"], r["how"]) for r in rows).items()):
        print(f"  {r} {s} ({h}): {n}")

EMIT_SPORTS = {"Padel", "Pickleball", "Badminton", "Squash", "Table Tennis"}
SITE_KINDS = {"pitch", "sports_centre", "fitness_centre", "sports_hall", "sports", "indoor_play", "stadium"}
STREET = re.compile(r"^(calle|avenida|av\.|privada|paseo|callej|andador|cerrada|camino|boulevard)", re.I)
RESORT_ONLY = {"node/14353121798", "way/1395779623", "way/1332651332"}   # ping pong tables inside Playa del Carmen / Cancun resorts (guests)
WALL = re.compile(r"front[oó]n|frontenis", re.I)


def keep_for_pin(r: dict) -> bool:
    """Which candidates become tag-only pins: a sport= tag of the right sport, or a sporty name on a sports feature."""
    if r["sport"] not in EMIT_SPORTS or STREET.match(r["name"]) or WALL.search(r["name"]):
        return False
    if r["how"] == "sport=" or r["sport_tag"]:
        if r["sport"] == "Badminton":
            return r["sport_tag"].strip() == "badminton" and (r["nearest_m"] == "" or int(r["nearest_m"]) >= 250)
        return r["sport"] in ("Padel", "Pickleball", "Table Tennis", "Squash") and r["kind"] in SITE_KINDS | {""}
    return r["how"] == "name" and r["kind"] in SITE_KINDS and "squash blossom" not in r["name"].lower()


def cmd_emit(args) -> None:
    """Cluster the kept candidates (same sport within 150 m = one pin) into manual_venues.csv rows, tag-only and labelled inferred."""
    rows = [r for r in csv.DictReader((Path(args.out) / args.file).open(encoding="utf-8")) if r["region"] == args.region and keep_for_pin(r)]
    d = json.loads(VENUES.read_text(encoding="utf-8"))
    pins = [(v["y"], v["x"], v["c"]) for v in d["venues"] if v["r"] == args.region and v.get("c")]
    existing = {x["venue_key"] for x in csv.DictReader((ROOT / "transform/seeds/manual_venues.csv").open(encoding="utf-8", newline=""))}
    clusters: list[list[dict]] = []
    for r in sorted(rows, key=lambda r: (r["sport"], r["lat"])):
        for c in clusters:
            if c[0]["sport"] == r["sport"] and metres(float(c[0]["lat"]), float(c[0]["lon"]), float(r["lat"]), float(r["lon"])) <= 150:
                c.append(r)
                break
        else:
            clusters.append([r])
    out = []
    for c in clusters:
        lat = round(sum(float(r["lat"]) for r in c) / len(c), 5)
        lon = round(sum(float(r["lon"]) for r in c) / len(c), 5)
        sport = c[0]["sport"]
        name = next((r["name"] for r in c if r["name"]), "")
        near = min(pins, key=lambda p: metres(lat, lon, p[0], p[1]))
        city = next((r["city"] for r in c if r["city"]), "") or (near[2] if metres(lat, lon, near[0], near[1]) < 15000 else "")
        label = name or f"{sport} courts ({city or 'unnamed'})"
        key = re.sub(r"[^a-z0-9]+", "-", f"{label}-{sport}-{city}".lower().encode("ascii", "ignore").decode()).strip("-")[:80]
        if key in existing:
            continue
        ids = ", ".join(r["osm"].replace("/", " ") for r in c[:6]) + ("…" if len(c) > 6 else "")
        tag = c[0]["sport_tag"] or "name only"
        basis = f"sport={tag}" if c[0]["sport_tag"] else f"its name ('{name}')"
        out.append({"venue_key": key, "venue_name": label, "sport": sport, "city": city, "lat": lat, "lon": lon,
                    "location_precision": f"{len(c)} OpenStreetMap feature{'s' if len(c) > 1 else ''} ({ids}); point approximate",
                    "website": "", "surface_type": "unknown", "setting": "unknown", "offerings": "", "courts": "", "access": "unknown",
                    "rules": f"Mapped on OpenStreetMap ({basis}).{' Hotel court: guests-only access is likely, not confirmed.' if re.search('hotel', label, re.I) else ''} No page was read: whether the courts are in use, their count, hours, cost, who may play and the sport are not confirmed.",
                    "confirmation": "reported", "confirmed_on": args.date,
                    "evidence": f"OpenStreetMap, keyword/tag Overpass sweep {args.date} ({args.region}; {ids}); no pin for {sport} within 200 m. Tags only; no page for this venue was read. City is from the nearest pin or OSM addr:city, inferred.",
                    "region": args.region})
    outp = Path(args.out) / f"seed_rows_{args.region}.csv"
    with outp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]) if out else ["venue_key"], lineterminator="\r\n")
        w.writeheader()
        w.writerows(out)
    print(f"{len(out)} rows -> {outp}")
    for r in out:
        print(f"  {r['sport']:12} {r['venue_name'][:45]:45} {r['city'][:18]:18} {r['lat']},{r['lon']} {r['location_precision'][:22]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("query")
    q.add_argument("--region", nargs="*", choices=REGIONS)
    q.add_argument("--out", required=True)
    q.add_argument("--tags-only", action="store_true", help="only sport=pickleball/table_tennis (skipped in the keyword run)")
    q.set_defaults(fn=cmd_query)
    df = sub.add_parser("diff")
    df.add_argument("--region", nargs="*", choices=REGIONS)
    df.add_argument("--out", required=True)
    df.add_argument("--tags-only", action="store_true")
    df.add_argument("--radius", type=float, default=200)
    df.set_defaults(fn=cmd_diff)
    em = sub.add_parser("emit")
    em.add_argument("--out", required=True)
    em.add_argument("--region", default="MX")
    em.add_argument("--file", default="candidates.csv")
    em.add_argument("--date", default="2026-11-23")
    em.set_defaults(fn=cmd_emit)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
