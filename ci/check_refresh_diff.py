"""Classify a refresh branch against ADR 0019 class R0 and its diff cap (gates 2 and 3). No LLM, no network.

Run from the repo root after `make app-data`, before opening the PR:

    python ci/check_refresh_diff.py --base-ref origin/main

Prints `R0` (exit 0) or `R3 escalate` with the reasons (exit 1). The agent still opens the PR in the second case
(stage 0), but labels it R3 and lists the reasons under "needs owner decision".
R0 = every changed file is on the allowlist, venues added + removed <= 2% of the base count, venues with a changed
field <= 5%. Venue count drop <= 1% is also checked here (the scorecard check repeats it from the trend line).
"""
import argparse, fnmatch, json, subprocess, sys
from pathlib import Path

ALLOW = [  # files an R0 refresh may touch (generated outputs, the trend line, the log, the session note)
    "app/data/venues.json",
    "app/data/build_stats.json",                # make stats (numbers on the How it's built page)
    "docs/data_quality.md",
    "docs/data_quality_trend.csv",
    "docs/coverage_snapshot.md",
    "docs/sport_name_review.md",
    "docs/agent_log.csv",
    "docs/sessions/*-refresh-run.md",
    "transform/seeds/all_racquet.csv",          # make sync-sports (the sheet is the source)
    "transform/seeds/osm_sport_map.csv",        # make sport-map
    "transform/seeds/sport_search_terms.csv",   # make search-terms
    "transform/seeds/venue_place_boundary.csv", # make city-boundaries
    "transform/seeds/nominatim_addresses.csv",  # make reverse-geocode (capped lookups)
]
MAX_ADD_REMOVE_PCT = 2.0
MAX_CHANGED_PCT = 5.0
MAX_DROP_PCT = 1.0


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def venues_at(ref):
    if ref is None:
        text = Path("app/data/venues.json").read_text(encoding="utf-8")
    else:
        text = git("show", f"{ref}:app/data/venues.json")
    return {v["i"]: v for v in json.loads(text)["venues"]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-ref", default="origin/main")
    args = ap.parse_args()

    reasons = []
    changed = set(git("diff", "--name-only", args.base_ref).split()) | set(git("ls-files", "--others", "--exclude-standard").split())
    for path in sorted(changed):
        if not any(fnmatch.fnmatch(path, pat) for pat in ALLOW):
            reasons.append(f"file outside the R0 allowlist: {path}")

    old, new = venues_at(args.base_ref), venues_at(None)
    added, removed = len(new.keys() - old.keys()), len(old.keys() - new.keys())
    modified = sum(1 for k in old.keys() & new.keys() if old[k] != new[k])
    base = len(old) or 1
    ar_pct, mod_pct, drop_pct = 100 * (added + removed) / base, 100 * modified / base, 100 * max(0, len(old) - len(new)) / base
    print(f"venues {len(old)} -> {len(new)}: +{added} -{removed} ({ar_pct:.2f}%), {modified} changed ({mod_pct:.2f}%), drop {drop_pct:.2f}%")
    if ar_pct > MAX_ADD_REMOVE_PCT:
        reasons.append(f"venues added + removed {ar_pct:.2f}% > {MAX_ADD_REMOVE_PCT}%")
    if mod_pct > MAX_CHANGED_PCT:
        reasons.append(f"venues with a changed field {mod_pct:.2f}% > {MAX_CHANGED_PCT}%")
    if drop_pct > MAX_DROP_PCT:
        reasons.append(f"venue count fell {drop_pct:.2f}% > {MAX_DROP_PCT}%")

    if reasons:
        print("R3 escalate:")
        for r in reasons:
            print("  -", r)
        sys.exit(1)
    print(f"R0 ok: {len(changed)} changed file(s), all on the allowlist, inside the diff cap")


if __name__ == "__main__":
    main()
