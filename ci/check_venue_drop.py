"""Fail when the committed app/data/venues.json has far fewer venues than main's, in total or in any one region.

Why (2026-11-15): a cloud tournament run exported venues.json from a stale raw-data repo (no AZ/NM/HI/TX/MX files) and
the map lost 8,300 pins (23,168 -> 14,850); CI passed because check_export_fresh.py only checks the seeds. This compares
against origin/main (same idea as check_refresh_diff.py, which only gates the refresh routine). A drop above 10% of a
region (regions of 50+ venues) or of the total fails. A real removal: set ALLOW_VENUE_DROP=1 and say why in the PR.
Usage: python ci/check_venue_drop.py [--base-ref origin/main]
"""
import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

MAX_DROP_PCT = 10.0
MIN_REGION = 50


def counts(text: str) -> Counter:
    c = Counter()
    for line in text.splitlines():
        line = line.strip().rstrip(",")
        if not line.startswith('{"i":'):
            continue
        try:
            v = json.loads(line)
        except ValueError:
            continue
        c[v.get("r", "?")] += 1
    return c


def drops(old: Counter, new: Counter) -> list[str]:
    out = []
    pairs = [("total", sum(old.values()), sum(new.values()))] + [(r, old[r], new[r]) for r in sorted(old) if old[r] >= MIN_REGION]
    for name, o, n in pairs:
        if o and 100 * (o - n) / o > MAX_DROP_PCT:
            out.append(f"{name}: {o} -> {n} venues ({100 * (o - n) / o:.1f}% fewer, limit {MAX_DROP_PCT:.0f}%)")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-ref", default="origin/main")
    a = ap.parse_args()
    base = subprocess.run(["git", "show", f"{a.base_ref}:app/data/venues.json"], capture_output=True)
    if base.returncode != 0:
        print(f"venue drop check skipped: {a.base_ref} not available")
        sys.exit(0)
    problems = drops(counts(base.stdout.decode("utf-8", "replace")), counts(Path("app/data/venues.json").read_text(encoding="utf-8", errors="replace")))
    if problems and os.environ.get("ALLOW_VENUE_DROP") == "1":
        print("venue drop allowed by ALLOW_VENUE_DROP=1:\n  " + "\n  ".join(problems))
    elif problems:
        print("venues.json lost many venues compared with " + a.base_ref + ":\n  " + "\n  ".join(problems)
              + "\nLikely an export from incomplete raw data (cloud: data/raw missing a region). Reload the raw CSVs, rebuild, re-export."
              + "\nIf the removal is real: ALLOW_VENUE_DROP=1 and explain it in the PR.")
        sys.exit(1)
    else:
        print("venue counts hold against " + a.base_ref)
