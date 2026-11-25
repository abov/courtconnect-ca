"""Split app/data/venues.json into the two files the map loads: data/map.json first, data/details.json after.

Why (2026-11-25): phones downloaded and parsed the whole 6 MB venues.json before the map showed anything. The map needs
only what draws pins, the list, search and filters; addresses, website links, notes and ids wait until a popup opens.

- map.json: every top-level list of venues.json except `venues`, plus `vc` = the venues by column ("columnar"), in the same order:
  `q` as one string (one letter per venue), `dy`/`dx` = lat/lon in 1e-5 degrees as differences from the previous venue (small
  numbers compress well), `w` = indexes of venues with a website, every field every venue has as a list (`n` `c` `r` `f` `p` `o`),
  and every other field as a sparse {index: value} map (a missing key means "not known", so it stays missing). A field not listed
  in DETAIL goes here, so a new export field is never lost.
- details.json: the DETAIL fields the same way (`i` ids, `a`, `w` website URLs, `s`, ... ).
app/venue-data.js turns both back into venue objects; ci/test_split_data.js checks the round trip equals venues.json exactly.

Neither file is committed (.gitignore): venues.json stays the one source. `make app-data` and the Pages workflow run this.
Usage: python ingestion/split_app_data.py [--src app/data/venues.json] [--out app/data]
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DENSE = ("n", "c", "r", "f", "p")           # every venue has these
DETAIL = {"i", "a", "w", "ru", "ad", "ai", "ap", "h", "ns", "al", "cd", "ud", "cn", "rn", "s"}   # popup-only; `w` keeps a flag in map.json
SCALE = 100000                                # coordinates are exported with 5 decimals


def j(x) -> str:
    return json.dumps(x, ensure_ascii=False, separators=(",", ":"))


def to_int(v: float) -> int:
    n = round(v * SCALE)
    if n / SCALE != v:
        raise SystemExit(f"coordinate {v} has more than 5 decimals; raise SCALE in split_app_data.py and app/venue-data.js")
    return n


def split(doc: dict) -> tuple[dict, dict]:
    venues = doc["venues"]
    vc: dict = {"len": len(venues)}
    for k in DENSE:
        vc[k] = [v[k] for v in venues]
    vc["q"] = "".join(v["q"] for v in venues)
    if len(vc["q"]) != len(venues):
        raise SystemExit("every venue needs a one-letter q")
    dy, dx, py, px = [], [], 0, 0
    for v in venues:
        y, x = to_int(v["y"]), to_int(v["x"])
        dy.append(y - py); dx.append(x - px); py, px = y, x
    vc["dy"], vc["dx"] = dy, dx
    vc["w"] = [n for n, v in enumerate(venues) if v.get("w")]
    det: dict = {"len": len(venues), "i": [v["i"] for v in venues]}
    known = set(DENSE) | {"q", "y", "x", "i"}
    keys = {k for v in venues for k in v} - known
    for k in sorted(keys):
        dest = det if k in DETAIL else vc
        if dest is vc and k in ("len", "q", "dy", "dx", "w"):
            raise SystemExit(f"venue field {k!r} clashes with a map.json column name; rename it in split_app_data.py and app/venue-data.js")
        if all(k in v for v in venues):
            dest[k] = [v[k] for v in venues]                              # on every venue (a, w, o, s): a plain column
        else:
            dest[k] = {n: v[k] for n, v in enumerate(venues) if k in v}   # absent means "not known", so keep it absent
    core = {k: val for k, val in doc.items() if k != "venues"}
    core["vc"] = vc
    return core, det


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", default=str(ROOT / "app" / "data" / "venues.json"))
    ap.add_argument("--out", default=str(ROOT / "app" / "data"))
    a = ap.parse_args()
    doc = json.loads(Path(a.src).read_text(encoding="utf-8"))
    core, det = split(doc)
    out = Path(a.out)
    (out / "map.json").write_text(j(core), encoding="utf-8")
    (out / "details.json").write_text(j(det), encoding="utf-8")
    print(f"map.json {(out / 'map.json').stat().st_size:,} bytes, details.json {(out / 'details.json').stat().st_size:,} bytes "
          f"({len(doc['venues']):,} venues; from {Path(a.src).name}, {Path(a.src).stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
