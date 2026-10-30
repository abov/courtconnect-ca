"""Point a fresh clone of this repo at your own area (docs/fork_guide.md steps 1 and 2).

    python ingestion/init_fork.py --region TX texas 25.8 -106.7 36.6 -93.5 114690            # dry run: prints what would change
    python ingestion/init_fork.py --region TX texas 25.8 -106.7 36.6 -93.5 114690 --apply    # does it

--region CODE NAME SOUTH WEST NORTH EAST OSM_RELATION   (repeat for more regions; NAME is the --area value, the relation is the
                                                        OSM border relation id, found on the region's openstreetmap.org page)
--metro KEY SOUTH WEST NORTH EAST CODE[,CODE]           (optional named sub-area for quick trial runs, e.g. --metro austin 30.1 -97.95 30.5 -97.55 TX)

What it does: rewrites ingestion/regions.json for your regions, and empties (header row kept) the seed files that hold the
original owner's California/Nevada research, so none of it is presented as yours. What it leaves alone, on purpose: the
mapping seeds (sports, categories, aliases), ci/gold and ci/fixtures (CA/NV samples: swap them, see the guide), the sports sheet
and keys. It refuses to apply on a git tree with uncommitted changes, so `git checkout .` undoes it.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Seeds that hold CA/NV research (docs/fork_guide.md step 2). Patterns are matched in transform/seeds.
OWNER_SEEDS = [
    "manual_venues", "manual_walls", "venue_actions", "venue_confirmations", "venue_leads", "watch_events", "social_events",
    "player_groups", "closed_places", "venue_court_counts", "place_sport_overrides", "osm_court_sport_overrides",
    "venue_*_official", "website_overrides", "nominatim_addresses", "venue_place_boundary", "search_interest", "search_metros",
    # keyed by CA/NV venue ids or places: meaningless in another area
    "court_group_merge", "manual_venue_no_merge", "manual_venue_sport_blocks", "place_no_group", "osm_wall_overrides",
    "venue_opening_status",
]


def parse_regions(specs: list[list[str]]) -> dict:
    regions = {}
    for code, name, s, w, n, e, rel in specs:
        s, w, n, e = map(float, (s, w, n, e))
        if not (-90 <= s < n <= 90 and -180 <= w < e <= 180):
            raise SystemExit(f"region {code}: bbox must be south < north within -90..90 and west < east within -180..180")
        if not re.fullmatch(r"[A-Za-z0-9]{1,4}", code) or code in regions:
            raise SystemExit(f"region code {code!r} must be 1-4 letters or digits and used once")
        if not re.fullmatch(r"[a-z0-9_]+", name):
            raise SystemExit(f"region name {name!r} must be lowercase letters, digits or underscores (it is the --area value)")
        if not rel.isdigit():
            raise SystemExit(f"region {code}: the OSM relation must be a number, got {rel!r}")
        regions[code] = {"name": name, "bbox": [s, w, n, e], "relation": int(rel), "cache": f"{code.lower()}_border.wkt"}
    return regions


def parse_metros(specs: list[list[str]], regions: dict) -> dict:
    metros = {}
    for key, s, w, n, e, codes in specs:
        codes = codes.split(",")
        unknown = [c for c in codes if c not in regions]
        if unknown or not re.fullmatch(r"[a-z0-9_]+", key):
            raise SystemExit(f"metro {key}: needs a lowercase key and region codes from --region (unknown: {unknown})")
        metros[key] = {"bbox": [float(s), float(w), float(n), float(e)], "states": codes}
    return metros


def seed_files(root: Path) -> list[Path]:
    seeds = root / "transform" / "seeds"
    found = {p for pat in OWNER_SEEDS for p in seeds.glob(pat + ".csv")}
    return sorted(found)


def apply(root: Path, regions: dict, metros: dict, write: bool) -> list[str]:
    """Return the list of changes; write them only when `write` is true."""
    out = []
    cfg_path = root / "ingestion" / "regions.json"
    old = json.loads(cfg_path.read_text(encoding="utf-8"))
    new = {"note": old.get("note", ""), "regions": regions, "metros": metros}
    out.append(f"ingestion/regions.json: regions {', '.join(old['regions'])} -> {', '.join(regions)}; metros {len(old['metros'])} -> {len(metros)}")
    if write:
        cfg_path.write_text(json.dumps(new, indent=1) + "\n", encoding="utf-8")
    for p in seed_files(root):
        lines = p.read_text(encoding="utf-8").splitlines()
        rows = max(0, len(lines) - 1)
        if rows:
            out.append(f"{p.relative_to(root).as_posix()}: {rows} row(s) removed, header kept")
            if write:
                p.write_text(lines[0] + "\n", encoding="utf-8")
    return out


def tree_is_clean(root: Path) -> bool:
    try:
        r = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, encoding="utf-8", check=True)
    except (OSError, subprocess.CalledProcessError):
        return True  # not a git checkout (a downloaded copy): nothing to protect
    return not r.stdout.strip()


NEXT = """Next (docs/fork_guide.md):
  1. ci/check_regions.py: replace the CA/NV test points with places inside and outside your area, then run it.
  2. ci/gold and ci/fixtures are California samples: swap them, or the match check and the CI build mean little for you.
  3. Sports: edit transform/seeds/all_racquet.csv directly (skip `make sync-sports`).
  4. Set COURTCONNECT_USER_AGENT, the title/analytics code in app/index.html, and GitHub Pages.
  5. make setup && make extract --area <your metro> for a quick trial, then make load build app-data."""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--region", nargs=7, action="append", required=True, metavar=("CODE", "NAME", "S", "W", "N", "E", "RELATION"), help="see above (7 values)")
    ap.add_argument("--metro", nargs=6, action="append", default=[], metavar=("KEY", "S", "W", "N", "E", "CODES"), help="see above (6 values)")
    ap.add_argument("--apply", action="store_true", help="write the changes (default: print them)")
    ap.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = ap.parse_args()

    regions = parse_regions(args.region)
    metros = parse_metros(args.metro, regions)
    if args.apply and not tree_is_clean(args.root):
        sys.exit("The git tree has uncommitted changes. Commit or stash them first, so `git checkout .` can undo this.")
    for line in apply(args.root, regions, metros, write=args.apply):
        print(("changed  " if args.apply else "would change  ") + line)
    print(NEXT if args.apply else "\nDry run only. Add --apply to make these changes.")


if __name__ == "__main__":
    main()
