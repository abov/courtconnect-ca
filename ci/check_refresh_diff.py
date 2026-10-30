"""Classify a refresh branch against ADR 0019 class R0 and its diff cap (gates 2 and 3). No LLM, no network.

Run from the repo root after `make app-data`, before opening the PR:

    python ci/check_refresh_diff.py --base-ref origin/main

Prints `R0` (exit 0) or `R3 escalate` with the reasons (exit 1). The agent still opens the PR in the second case
(stage 0), but labels it R3 and lists the reasons under "needs owner decision".
R0 = every changed file is on the allowlist, venues added + removed <= 2% of the base count, venues with a changed
field <= 5%. Venue count drop <= 1% is also checked here (the scorecard check repeats it from the trend line).
Every other top-level array of the export (events, social, walls, platforms, sports) is diffed too, and any URL
that appears in the new export but not the old one is counted: a link swap is the cheapest way to misuse a refresh
(docs/merge_gate_threat_model.md, gaps 2 and 3). The caps below were set from past refresh commits (the 2026-10
monthly refresh changed 12 of 90 events and put a new URL on 38 of 10,266 surviving venues).
"""
import argparse, fnmatch, json, subprocess, sys
from collections import Counter
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
MAX_URL_VENUES_PCT = 0.5     # surviving venues that gain a URL they did not have (website or link-out)
MAX_ROWS_PCT_OTHER = 20.0    # events / social / walls / platforms rows added, removed or changed (floor MIN_ROWS_OTHER)
MIN_ROWS_OTHER = 5
MAX_NEW_URLS_OTHER = 5       # new URLs per non-venue array; sports is only URL-checked (counts and blurbs follow the sheet)
ROWS_UNCHECKED = {"sports"}


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", check=True).stdout


def export_at(ref):
    if ref is None:
        text = Path("app/data/venues.json").read_text(encoding="utf-8")
    else:
        text = git("show", f"{ref}:app/data/venues.json")
    return json.loads(text)


def urls_in(obj, out=None):
    """Every http(s) string anywhere inside a row, as a Counter (covers `w`, `u`, `k`, `g` and the nested `ac` link-outs)."""
    out = Counter() if out is None else out
    if isinstance(obj, str):
        if obj.startswith(("http://", "https://")):
            out[obj] += 1
    elif isinstance(obj, list):
        for x in obj:
            urls_in(x, out)
    elif isinstance(obj, dict):
        for x in obj.values():
            urls_in(x, out)
    return out


def canon(row):
    return json.dumps(row, sort_keys=True)


def classify_exports(old, new):
    """Compare two parsed exports. Returns (summary lines, reasons to escalate)."""
    lines, reasons = [], []
    ov, nv = {v["i"]: v for v in old["venues"]}, {v["i"]: v for v in new["venues"]}
    added, removed = len(nv.keys() - ov.keys()), len(ov.keys() - nv.keys())
    modified = sum(1 for k in ov.keys() & nv.keys() if ov[k] != nv[k])
    url_rows = sum(1 for k in ov.keys() & nv.keys() if urls_in(nv[k]) - urls_in(ov[k]))
    base = len(ov) or 1
    ar_pct, mod_pct = 100 * (added + removed) / base, 100 * modified / base
    drop_pct, url_pct = 100 * max(0, len(ov) - len(nv)) / base, 100 * url_rows / base
    lines.append(f"venues {len(ov)} -> {len(nv)}: +{added} -{removed} ({ar_pct:.2f}%), {modified} changed ({mod_pct:.2f}%), "
                 f"drop {drop_pct:.2f}%, {url_rows} gained a URL ({url_pct:.2f}%)")
    if ar_pct > MAX_ADD_REMOVE_PCT:
        reasons.append(f"venues added + removed {ar_pct:.2f}% > {MAX_ADD_REMOVE_PCT}%")
    if mod_pct > MAX_CHANGED_PCT:
        reasons.append(f"venues with a changed field {mod_pct:.2f}% > {MAX_CHANGED_PCT}%")
    if drop_pct > MAX_DROP_PCT:
        reasons.append(f"venue count fell {drop_pct:.2f}% > {MAX_DROP_PCT}%")
    if url_pct > MAX_URL_VENUES_PCT:
        reasons.append(f"{url_rows} existing venues gained a URL ({url_pct:.2f}% > {MAX_URL_VENUES_PCT}%)")

    for key in sorted((old.keys() | new.keys()) - {"venues"}):
        orows, nrows = old.get(key), new.get(key)
        if not (isinstance(orows, list) or isinstance(nrows, list)):
            continue  # meta and other scalars: counts that follow the arrays
        orows, nrows = orows or [], nrows or []
        oc, nc = Counter(map(canon, orows)), Counter(map(canon, nrows))
        gained, lost = sum((nc - oc).values()), sum((oc - nc).values())
        cap = max(MIN_ROWS_OTHER, int(len(orows) * MAX_ROWS_PCT_OTHER / 100))
        new_urls = sum((urls_in(nrows) - urls_in(orows)).values())
        lines.append(f"{key} {len(orows)} -> {len(nrows)}: {gained} rows new or changed, {lost} gone, {new_urls} new URL(s)")
        if key not in ROWS_UNCHECKED and max(gained, lost) > cap:
            reasons.append(f"{key}: {max(gained, lost)} rows added, removed or changed > {cap}")
        if new_urls > MAX_NEW_URLS_OTHER:
            reasons.append(f"{key}: {new_urls} new URLs > {MAX_NEW_URLS_OTHER}")
    return lines, reasons


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-ref", default="origin/main")
    args = ap.parse_args()

    reasons = []
    changed = set(git("diff", "--name-only", args.base_ref).split()) | set(git("ls-files", "--others", "--exclude-standard").split())
    for path in sorted(changed):
        if not any(fnmatch.fnmatch(path, pat) for pat in ALLOW):
            reasons.append(f"file outside the R0 allowlist: {path}")

    lines, export_reasons = classify_exports(export_at(args.base_ref), export_at(None))
    print("\n".join(lines))
    reasons += export_reasons

    if reasons:
        print("R3 escalate:")
        for r in reasons:
            print("  -", r)
        sys.exit(1)
    print(f"R0 ok: {len(changed)} changed file(s), all on the allowlist, inside the diff cap")


if __name__ == "__main__":
    main()
