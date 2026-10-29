"""Build the public change feed app/data/changes.json: what differs between two exports (ADR 0025 step 1, ADR 0026).

    python ingestion/build_changes.py                      # new venues.json vs the one on origin/main (run in the refresh PR)
    python ingestion/build_changes.py --base-ref <ref>     # compare with another commit
    python ingestion/build_changes.py --check              # CI: feed is well formed and venue ids did not drift

No personal data: the feed is derived only from the public export. The previous feed is read from the base ref and kept
for HISTORY_DAYS, so rerunning on the same refresh is idempotent. A raw diff is not proof of a change in the world
(an OSM edit, a new Overture release, a rule change all move it), so the feed says what the DATA now says and carries
the data's own label: confirmed (cf v/o), reported (cf r), inferred (everything else).

Row shape: {d date, k kind, i venue id (venues only), n name, c city, l label, t detail}
  kinds: venue_new, venue_gone, venue_changed, event_new, event_changed, event_removed (only events that had not ended), social_new, social_removed
Venue ids that vanish and reappear under another id at the same name within ID_DRIFT_M metres are counted as id drift
(favorites would stop matching), not as a new+gone pair; --check fails when drift passes MAX_ID_DRIFT of venues.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

VENUES = Path("app/data/venues.json")
OUT = Path("app/data/changes.json")
HISTORY_DAYS = 180
ID_DRIFT_M = 200
MAX_ID_DRIFT = 0.02
KINDS = {"venue_new", "venue_gone", "venue_changed", "event_new", "event_changed", "event_removed", "social_new", "social_removed"}


def load_ref(ref: str, path: Path) -> dict | None:
    """The file as committed at `ref` (None when it did not exist there)."""
    r = subprocess.run(["git", "show", f"{ref}:{path.as_posix()}"], capture_output=True, text=True, encoding="utf-8")
    return json.loads(r.stdout) if r.returncode == 0 else None


def name(v: dict) -> str:
    return v.get("n") or "(unnamed)"


def label(v: dict) -> str:
    return {"v": "confirmed", "o": "confirmed", "r": "reported"}.get(v.get("cf", ""), "inferred")


def metres(a: dict, b: dict) -> float:
    dy = (a["y"] - b["y"]) * 111_320
    dx = (a["x"] - b["x"]) * 111_320 * math.cos(math.radians(a["y"]))
    return math.hypot(dx, dy)


def sport_courts(v: dict, sports: list) -> dict:
    return {sports[p[0]]["n"]: p[1] for p in v.get("p", [])}


def venue_detail(old: dict, new: dict, osp: list, nsp: list) -> list[str]:
    out = []
    if old.get("n") != new.get("n"):
        out.append(f"name: {name(old)} -> {name(new)}")
    oc, nc = sport_courts(old, osp), sport_courts(new, nsp)
    if added := sorted(set(nc) - set(oc)):
        out.append("sports added: " + ", ".join(added))
    if dropped := sorted(set(oc) - set(nc)):
        out.append("sports removed: " + ", ".join(dropped))
    for s in sorted(set(oc) & set(nc)):
        if oc[s] and nc[s] and oc[s] != nc[s]:
            out.append(f"{s} courts: {oc[s]} -> {nc[s]}")
    if old.get("xu", 0) != new.get("xu", 0):
        out.append("access: " + ("public access not confirmed" if new.get("xu") else "public access confirmed"))
    if old.get("up") != new.get("up"):
        out.append(f"opening status: {old.get('up', 'open')} -> {new.get('up', 'open')}")
    if old.get("cf") != new.get("cf"):
        out.append(f"confirmation: {old.get('cf', 'none')} -> {new.get('cf', 'none')}")
    return out


def venue_changes(old: dict, new: dict, day: str) -> tuple[list[dict], dict]:
    ov, nv = {v["i"]: v for v in old["venues"]}, {v["i"]: v for v in new["venues"]}
    added, gone = [i for i in nv if i not in ov], [i for i in ov if i not in nv]
    by_name: dict[str, list[str]] = {}
    for i in gone:
        by_name.setdefault((ov[i].get("n") or "").lower(), []).append(i)
    drift, drift_new, drift_old = [], set(), set()
    for i in added:
        for j in by_name.get((nv[i].get("n") or "").lower(), []):
            if j not in drift_old and metres(ov[j], nv[i]) <= ID_DRIFT_M:
                drift.append([j, i, nv[i].get("n") or ""])
                drift_new.add(i)
                drift_old.add(j)
                break
    rows = []
    for i in added:
        if i not in drift_new:
            v = nv[i]
            sp = ", ".join(sorted(sport_courts(v, new["sports"])))
            rows.append({"d": day, "k": "venue_new", "i": i, "n": name(v), "c": v.get("c") or "", "l": label(v), "t": sp})
    for i in gone:
        if i not in drift_old:
            v = ov[i]
            rows.append({"d": day, "k": "venue_gone", "i": i, "n": name(v), "c": v.get("c") or "", "l": label(v),
                         "t": "no longer listed (the source stopped listing it or it stopped matching; a lead, not proof it closed)"})
    for i in nv.keys() & ov.keys():
        det = venue_detail(ov[i], nv[i], old["sports"], new["sports"])
        if det:
            rows.append({"d": day, "k": "venue_changed", "i": i, "n": name(nv[i]), "c": nv[i].get("c") or "", "l": label(nv[i]),
                         "t": "; ".join(det)})
    stats = {"venues_old": len(ov), "venues_new": len(nv), "id_drift": len(drift), "id_drift_examples": drift[:10]}
    return rows, stats


def keyed(rows: list[dict], *fields: str) -> dict:
    return {tuple(r.get(f, "") for f in fields): r for r in rows}


def event_changes(old: dict, new: dict, day: str) -> list[dict]:
    oe, ne = keyed(old["events"], "n", "c"), keyed(new["events"], "n", "c")
    rows = []
    for k, e in ne.items():
        det = {"label": "confirmed" if e.get("d") == "confirmed" else "reported"}
        if k not in oe:
            rows.append({"d": day, "k": "event_new", "n": e["n"], "c": e.get("c", ""), "l": det["label"],
                         "t": f"{e.get('sp', '')}, {e.get('s', '')} to {e.get('e', '')}, {e.get('v', '')}"})
            continue
        o = oe[k]
        diff = [f"{name}: {o.get(f, '')} -> {e.get(f, '')}" for f, name in
                (("s", "start"), ("e", "end"), ("d", "date status"), ("v", "venue")) if o.get(f, "") != e.get(f, "")]
        if diff:
            rows.append({"d": day, "k": "event_changed", "n": e["n"], "c": e.get("c", ""), "l": det["label"], "t": "; ".join(diff)})
    for k, o in oe.items():
        if k not in ne and (o.get("e") or o.get("s") or "") >= day:   # an event that simply ended is not a change
            rows.append({"d": day, "k": "event_removed", "n": o["n"], "c": o.get("c", ""), "l": "reported",
                         "t": "no longer listed before its end date (cancelled, moved, or the source dropped it)"})
    return rows


def social_changes(old: dict, new: dict, day: str) -> list[dict]:
    os_, ns = keyed(old["social"], "n", "o", "c"), keyed(new["social"], "n", "o", "c")
    rows = [{"d": day, "k": "social_new", "n": s["n"], "c": s.get("c", ""), "l": "reported", "t": f"{s.get('sp', '')}, {s.get('sc', '')}"}
            for k, s in ns.items() if k not in os_]
    rows += [{"d": day, "k": "social_removed", "n": s["n"], "c": s.get("c", ""), "l": "reported", "t": "no longer listed"}
             for k, s in os_.items() if k not in ns]
    return rows


def build(base_ref: str, day: str, new_path: Path) -> dict:
    old = load_ref(base_ref, VENUES)
    if old is None:
        sys.exit(f"{VENUES} does not exist at {base_ref}")
    new = json.loads(new_path.read_text(encoding="utf-8"))
    vrows, stats = venue_changes(old, new, day)
    rows = vrows + event_changes(old, new, day) + social_changes(old, new, day)
    prior = (load_ref(base_ref, OUT) or {}).get("changes", [])
    cutoff = (date.fromisoformat(day) - timedelta(days=HISTORY_DAYS)).isoformat()
    keep = [r for r in prior if r["d"] >= cutoff and r["d"] != day]
    changes = sorted(keep + rows, key=lambda r: (r["d"], r["k"], r.get("i", ""), r["n"]), reverse=True)
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["k"]] = counts.get(r["k"], 0) + 1
    meta = {"generated": day, "base": base_ref, "history_days": HISTORY_DAYS, "this_run": counts, **stats,
            "note": "Derived only from the public export. A change is what the data now says, not proof of a change on the ground; labels are the data's own."}
    return {"meta": meta, "changes": changes}


def check(feed: dict, base_ref: str | None) -> list[str]:
    problems = []
    for r in feed.get("changes", []):
        if r.get("k") not in KINDS or not r.get("d") or not r.get("n") or r.get("l") not in ("confirmed", "reported", "inferred"):
            problems.append(f"malformed row: {r}")
        if r.get("d", "") > date.today().isoformat():
            problems.append(f"row dated in the future: {r}")
    text = json.dumps(feed)
    if re.search(r"[\w.+-]+@[\w-]+\.\w+", text):
        problems.append("feed contains an email address (none belongs here)")
    if base_ref and VENUES.exists():
        old = load_ref(base_ref, VENUES)
        if old:
            _, stats = venue_changes(old, json.loads(VENUES.read_text(encoding="utf-8")), "1970-01-01")
            if stats["id_drift"] > MAX_ID_DRIFT * max(stats["venues_old"], 1):
                problems.append(f"venue id drift {stats['id_drift']} of {stats['venues_old']} (> {MAX_ID_DRIFT:.0%}): favorites would stop matching; examples {stats['id_drift_examples']}")
    return problems


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-ref", default="origin/main")
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        if not OUT.exists():
            sys.exit(f"{OUT} is missing; run python ingestion/build_changes.py")
        problems = check(json.loads(OUT.read_text(encoding="utf-8")), a.base_ref)
        if problems:
            sys.exit("Change feed problems:\n- " + "\n- ".join(problems))
        print("Change feed OK.")
        return
    feed = build(a.base_ref, a.date, VENUES)
    OUT.write_text(json.dumps(feed, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    m = feed["meta"]
    print(f"Wrote {OUT}: {len(feed['changes'])} rows kept; this run {m['this_run'] or 'none'}; id drift {m['id_drift']} of {m['venues_old']}")


if __name__ == "__main__":
    main()
