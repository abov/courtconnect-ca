"""Rank which venues are worth rechecking next, so freshness costs a fixed budget instead of growing with the map.

    python ingestion/rank_rechecks.py                       # top 100 -> docs/recheck_queue.csv
    python ingestion/rank_rechecks.py --top 25
    python ingestion/rank_rechecks.py --budget-usd 2 --usd-per-recheck 0.05     # top N = budget / cost (the smaller of the two caps wins)
    python ingestion/rank_rechecks.py --viewed-only         # drop venues with no traffic signal at all

Score = expected harm = (views + floor) x p_change.
  views     how often visitors looked at the venue in the last --days days, from the committed docs/usage_events.csv (no token needed).
            Today the map only reports the venue's CITY (`demand-where`), so a venue gets its city's views divided by the venues
            there (traffic_basis = city). When the map sends `venue-view/<venue_id>` (docs/recheck_queue_plan.md) those views are used
            as they are (traffic_basis = venue). Venues with neither get the small floor, so they only fill the queue when nothing
            viewed is left, and `--viewed-only` removes them: an unviewed venue then costs nothing.
  p_change  a rough chance that something a visitor relies on (open, courts, access) changed since the last good look. INFERRED from
            readable priors, not a trained or calibrated model: venue type x source x age of the last dated check, plus bumps for the
            "may be closed" lead (mart_venue_closure_signal) and the page-change status (data/raw/page_checks.csv). The numbers below are
            starting guesses; tune them when rechecks show how often a venue really changed.

The queue only ORDERS rechecks. It never edits a seed and never says a venue is closed; a person (or the page reader, ADR 0017) rereads
the venue's public page and re-dates the row. Needs the local warehouse (`make build`) and nothing else.
"""
from __future__ import annotations

import argparse
import csv
import math
import re
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import duckdb
from rawdir import raw_path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "courtconnect.duckdb"
EVENTS = ROOT / "docs" / "usage_events.csv"
OUT = ROOT / "docs" / "recheck_queue.csv"

# --- priors (inferred starting guesses; every number here shows up in the `reasons` column of the queue) ---
TYPE_BASE = {"commercial": 0.25, "unknown": 0.15, "public": 0.08}     # yearly chance of a change a visitor would notice
SOURCE_MULT = {"visited": 0.5, "official": 0.6, "link_verified": 0.6, "reported": 0.9,
               "osm+places": 1.0, "osm": 1.1, "walls": 0.8, "manual": 1.0, "places_only": 1.3}
AGE_MULT = [(3, 0.4), (6, 0.7), (12, 1.0), (24, 1.5)]                  # months since the newest dated check; older 2.0
AGE_NEVER = 1.4                                                         # no dated check at all
CLOSURE_BUMP = 0.35                                                     # Overture dropped the venue's own place (inferred lead)
PAGE_BUMP = {"gone": 0.40, "changed": 0.25, "error": 0.05}
PAGE_UNCHANGED_MULT = 0.7                                               # its page was unchanged on the last look
P_MIN, P_MAX = 0.01, 0.95

COMMERCIAL_WORDS = re.compile(r"\b(club|academy|resort|fitness|racquet|racket|padel|pickleball|sports? (center|centre|complex)|tennis (center|centre)|athletic|health)\b", re.I)
PUBLIC_WORDS = re.compile(r"\b(park|playground|school|college|university|rec(reation)? (center|centre)|community|elementary|middle|high|library|city of|county)\b", re.I)
FIELDS = ["rank", "venue_id", "venue_name", "city", "region", "score", "p_change", "traffic_views", "traffic_basis", "venue_type", "source_basis",
          "last_checked_on", "age_months", "closure_signal", "page_status", "est_cost_usd", "reasons", "confirmation"]


def venue_type(name: str, kind: str, public: bool, members: bool, free: bool, access: str) -> tuple[str, str]:
    if kind == "hitting_wall":
        return "public", "hitting wall"
    if members or access in ("members", "club", "private"):
        return "commercial", "members/club access"
    if public or free or access == "public":
        return "public", "tagged public or free"
    if COMMERCIAL_WORDS.search(name or ""):
        return "commercial", "club-like name"
    if PUBLIC_WORDS.search(name or ""):
        return "public", "park/school-like name"
    return "unknown", "no type clue"


def age_mult(months: float | None) -> float:
    if months is None:
        return AGE_NEVER
    for limit, m in AGE_MULT:
        if months <= limit:
            return m
    return 2.0


def city_key(city: str, region: str) -> str:
    return re.sub(r"[^a-z0-9]", "", f"{city or ''}{region or ''}".lower())


def load_traffic(days: int) -> tuple[dict[str, int], dict[str, int], int]:
    """(views by venue_id, views by city key, total venue-open events) in the last `days` days from the committed rollup."""
    by_venue: dict[str, int] = defaultdict(int)
    by_city: dict[str, int] = defaultdict(int)
    opens = 0
    if not EVENTS.exists():
        return by_venue, by_city, opens
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    with EVENTS.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["day"] < cutoff:
                continue
            n = int(r["count"] or 0)
            if r["event"] == "venue-view":
                by_venue[r["detail"].strip().lower()] += n
            elif r["event"] == "demand-where":
                by_city[re.sub(r"[^a-z0-9]", "", r["detail"].lower())] += n
            elif r["event"] == "venue-open":
                opens += n
    return by_venue, by_city, opens


def load_page_status() -> dict[str, str]:
    """url -> status from data/raw/page_checks.csv (empty when check_page_changes.py has not run yet)."""
    p = Path(raw_path("page_checks.csv"))
    if not p.exists():
        return {}
    with p.open(encoding="utf-8", newline="") as f:
        return {r["url"]: r["status"] for r in csv.DictReader(f)}


PAGE_RANK = {"gone": 4, "changed": 3, "error": 2, "volatile": 1, "new": 1, "unchanged": 0}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--top", type=int, default=100, help="rows to write (default 100)")
    ap.add_argument("--budget-usd", type=float, default=0, help="cap by money instead: rows = budget / --usd-per-recheck")
    ap.add_argument("--usd-per-recheck", type=float, default=0.05, help="assumed cost of one page reread (a guess until measured; docs/recheck_queue_plan.md)")
    ap.add_argument("--days", type=int, default=60, help="traffic window in days (the GoatCounter export holds 60)")
    ap.add_argument("--floor", type=float, default=0.1, help="pseudo-views for a venue with no traffic signal")
    ap.add_argument("--viewed-only", action="store_true", help="leave out venues with no traffic signal (they cost nothing)")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    limit = args.top
    if args.budget_usd:
        limit = min(limit, math.floor(args.budget_usd / args.usd_per_recheck))

    con = duckdb.connect(str(DB), read_only=True)
    rows = con.execute("""
        select v.venue_id, v.venue_name, v.city, v.region, v.venue_source, v.venue_kind, coalesce(v.is_confirmed_public, false),
               coalesce(v.is_members_only, false), coalesce(v.has_free_courts, false), c.closure_signal
        from core.dim_venue v join marts.mart_venue_confidence c using (venue_id)""").fetchall()
    manual = {vid: (lvl, d, acc) for vid, lvl, d, acc in con.execute("""
        select mm.effective_venue_id,
               arg_max(m.confirmation_level, coalesce(m.confirmed_on, date '1900-01-01')),
               max(m.confirmed_on),
               max(case m.access_type when 'public' then 'public' else m.access_type end)
        from staging.stg_manual_venues m join intermediate.int_manual_venue_match mm using (venue_key) group by 1""").fetchall()}
    verified = dict(con.execute("select venue_id, max(verified_on) from marts.mart_venue_actions group by 1").fetchall())
    urls: dict[str, set[str]] = defaultdict(set)
    for vid, u in con.execute("select venue_id, url from marts.mart_venue_actions where url is not null").fetchall():
        urls[vid].add(u)
    for vid, u in con.execute("""select mm.effective_venue_id, m.website from staging.stg_manual_venues m
                                 join intermediate.int_manual_venue_match mm using (venue_key) where m.website is not null""").fetchall():
        urls[vid].add(u)

    pages = load_page_status()
    v_views, c_views, opens = load_traffic(args.days)
    per_city = defaultdict(int)
    for r in rows:
        per_city[city_key(r[2], r[3])] += 1
    attributed = sum(v_views.values())

    today = date.today()
    out, with_traffic_venue, with_traffic_city = [], 0, 0
    for vid, name, city, region, src, kind, public, members, free, closure in rows:
        lvl, mdate, acc = manual.get(vid, (None, None, ""))
        vdate = verified.get(vid)
        last = max([d for d in (mdate, vdate) if d], default=None)
        months = round((today - last).days / 30.4, 1) if last else None

        vtype, why_type = venue_type(name, kind, public, members, free, acc or "")
        basis = lvl if lvl in ("visited", "official", "reported") else ("link_verified" if vdate else src)
        why = [f"{vtype} ({why_type})"]
        p = TYPE_BASE[vtype] * SOURCE_MULT.get(basis, 1.0) * age_mult(months)
        why.append({"visited": "visited by a person", "official": "confirmed from the venue's own page", "reported": "community report only",
                    "link_verified": "link-out verified", "osm": "OpenStreetMap only", "osm+places": "OSM + Overture",
                    "places_only": "Overture business record only", "walls": "wall report", "manual": "hand-added, undated"}.get(basis, basis))
        why.append("never dated" if months is None else f"last checked {months:g} months ago")
        if closure:
            p += CLOSURE_BUMP
            why.append("Overture dropped its place (inferred may-be-closed lead)")
        st = max((pages[u] for u in urls.get(vid, ()) if u in pages), key=lambda s: PAGE_RANK.get(s, 0), default="")
        if st in PAGE_BUMP:
            p += PAGE_BUMP[st]
            why.append(f"page {st}")
        elif st == "unchanged":
            p *= PAGE_UNCHANGED_MULT
            why.append("page unchanged on last look")
        p = min(P_MAX, max(P_MIN, p))

        direct = v_views.get(vid, 0)
        city_share = c_views.get(city_key(city, region), 0) / per_city[city_key(city, region)] if per_city[city_key(city, region)] else 0
        if direct:
            views, tb = float(direct), "venue"
            with_traffic_venue += 1
        elif city_share:
            views, tb = city_share, "city"
            with_traffic_city += 1
        else:
            views, tb = 0.0, "none"
            if args.viewed_only:
                continue
        out.append({"venue_id": vid, "venue_name": name, "city": city or "", "region": region or "", "score": round((views + args.floor) * p, 4),
                    "p_change": round(p, 3), "traffic_views": round(views, 3), "traffic_basis": tb, "venue_type": vtype, "source_basis": basis,
                    "last_checked_on": last.isoformat() if last else "", "age_months": "" if months is None else months,
                    "closure_signal": closure or "", "page_status": st, "reasons": "; ".join(why), "confirmation": "inferred"})

    out.sort(key=lambda r: (-r["score"], -r["p_change"], r["venue_id"]))
    out = out[:limit]
    for i, r in enumerate(out, 1):
        r["rank"] = i
        r["est_cost_usd"] = round(i * args.usd_per_recheck, 2)       # cumulative: what rechecking down to this row costs
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)

    print(f"{len(rows):,} venues scored; traffic window {args.days} days: {opens} venue-open events, {attributed} attributed to a venue (venue-view), "
          f"{with_traffic_venue} venues with direct views, {with_traffic_city} via city share; pages checked: {len(pages):,}")
    print(f"wrote top {len(out)} -> {args.out}  (about ${len(out) * args.usd_per_recheck:.2f} at ${args.usd_per_recheck}/recheck)")
    for r in out[:10]:
        print(f"  {r['rank']:>3} {r['score']:>7} p={r['p_change']:<5} views={r['traffic_views']:<6} {r['venue_name'][:42]:<42} {r['city']}, {r['region']}  [{r['reasons']}]")


if __name__ == "__main__":
    main()
