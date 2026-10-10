"""Export the venue finder to a compact JSON file for the static map app (app/data/venues.json).

    python ingestion/export_app_data.py            (or: make app-data)

Deliberately NOT exported: phone numbers (some belong to individual instructors), Google IDs, and raw record ids.
Websites are exported only when `website_usable` is set, so dead links never reach the page.

File shape (kept small on purpose; ~2 MB for ~10,000 venues):
  meta    : counts, generation date, attribution
  sports  : [{n: name, v: venues, s: status, r: recommended next source}], ordered by venues found
  venues  : [{i, n, q, s, y, x, c, a, w, o, f, p:[[sportIndex, courts, flagMask], ...], ac, ru, xu}]
     ac link-outs [type,title,url,provider,start,end,price]; ru court rules (hand-curated map); xu 1 = public access not confirmed
  events  : [{n name, sp sport, l level, f watch format, v venue, c city, y, x, pr location precision, s start, e end, d date status,
              t ticket info, u info link, k tickets link, vo verified on}]   (events to WATCH; every one links out to the organizer)
     q name quality: c confirmed (court/operator name or hand-curated), p business listing, i inferred from nearby park/school, u unnamed
     s source: o OpenStreetMap, p places, b both, m hand-curated
     f venue bits: 1 lit, 2 public, 4 free      p[i][2] sport bits: 1 indoor, 2 outdoor, 4 sand, 8 clay, 16 grass, 32 hard, 64 turf
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import duckdb

OUT = Path("app/data/venues.json")
QUALITY = {"court_name": "c", "operator": "c", "manual": "c", "places_directory": "p", "enclosing_feature": "i", "unnamed": "u"}
SOURCE = {"osm": "o", "osm+places": "b", "places_only": "p", "manual": "m"}
OFFER_CODES = {"open_play": "O", "clinics": "C", "private_lessons": "L", "group_classes": "G", "drop_in": "D", "tournaments": "T",
               "leagues": "E", "social_events": "S"}
# venue_actions.action_type -> offering code (club_page is a plain link, not an offering)
ACTION_OFFER = {"open_play": "O", "clinic": "C", "private_lesson": "L", "group_class": "G", "drop_in": "D", "tournament": "T",
                "league": "E", "social_event": "S"}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    con = duckdb.connect("courtconnect.duckdb", read_only=True)

    gaps = con.execute("""
        select g.sport_name, g.coverage_status, g.venues_found, g.recommended_next_source
        from marts.mart_sport_gaps g order by g.venues_found desc, g.sport_name""").fetchall()
    sport_index = {r[0]: i for i, r in enumerate(gaps)}
    sports = [{"n": r[0], "v": int(r[2]), "s": r[1], "r": r[3]} for r in gaps]

    rows = con.execute("""
        select venue_id, venue_name, name_source, venue_source, sport_name, courts_for_sport, lat, lon, city, address_line,
               website_usable, offerings, has_indoor, has_outdoor, has_sand_beach, has_clay, has_grass, has_hard, has_turf,
               has_lit_courts, is_confirmed_public, has_free_courts
        from marts.mart_venue_finder""").fetchall()

    # Things to do at a venue: link-outs to the provider's own page (CourtConnect books nothing). Current ones only.
    actions: dict[str, list] = defaultdict(list)
    for vid, atype, title, provider, url, price, start, end in con.execute("""
            select venue_id, action_type, title, provider, url, price_info, start_date, end_date
            from marts.mart_venue_actions where is_current order by action_type, title""").fetchall():
        actions[vid].append([atype, title, url, provider, str(start) if start else "", str(end) if end else "", price or ""])

    # Notes from the hand-curated paddle tennis map: court rules, and whether public access is confirmed (merged venues included).
    manual = {}
    for vid, rules, unconfirmed in con.execute("""
            select mm.effective_venue_id, min(case when lower(m.rules_note) <> 'unknown' then m.rules_note end), max(case when m.access_type = 'unknown' then 1 else 0 end)
            from staging.stg_manual_venues m join intermediate.int_manual_venue_match mm on mm.venue_key = m.venue_key
            group by 1""").fetchall():
        manual[vid] = {"r": rules or "", "u": int(unconfirmed)}

    venues: dict[str, dict] = {}
    entries: dict[str, list] = defaultdict(list)
    for (vid, name, nsrc, vsrc, sport, courts, lat, lon, city, addr, web, offers, indoor, outdoor, sand, clay, grass, hard, turf,
         lit, public, free) in rows:
        if lat is None or lon is None:
            continue
        if vid not in venues:
            venues[vid] = {
                "i": vid[:10],
                "n": name if nsrc != "unnamed" else "",
                "q": QUALITY.get(nsrc, "u"),
                "s": SOURCE.get(vsrc, "o"),
                "y": round(float(lat), 5),
                "x": round(float(lon), 5),
                "c": city or "",
                "a": addr or "",
                "w": web or "",
                "o": "".join(OFFER_CODES[o] for o in (offers or "").split(";") if o in OFFER_CODES),
                "f": (1 if lit else 0) | (2 if public else 0) | (4 if free else 0),
            }
        mask = sum(bit for flag, bit in ((indoor, 1), (outdoor, 2), (sand, 4), (clay, 8), (grass, 16), (hard, 32), (turf, 64)) if flag)
        entries[vid].append([sport_index[sport], int(courts or 0), mask])
        venues[vid]["_o"] = venues[vid].get("_o", set()) | {c for c in (venues[vid]["o"] or "")}

    out_venues = []
    for vid, v in venues.items():
        v["p"] = sorted(entries[vid])
        codes = set(v.pop("_o", set())) | {ACTION_OFFER[a[0]] for a in actions.get(vid, []) if a[0] in ACTION_OFFER}
        v["o"] = "".join(sorted(codes))
        if actions.get(vid):
            v["ac"] = actions[vid]               # link-outs: [type, title, url, provider, start, end, price]
        if vid in manual:
            if manual[vid]["r"]:
                v["ru"] = manual[vid]["r"]       # court rules from the hand-curated map
            if manual[vid]["u"]:
                v["xu"] = 1                      # public access not confirmed on the source map
        out_venues.append(v)
    out_venues.sort(key=lambda v: (v["y"], v["x"]))

    # Watch events: link-out discovery only (nothing is sold or booked here). Dates stay ISO strings; the page hides past events itself.
    events = []
    for (name, sport, level, fmt, venue, city, lat, lon, prec, start, end, dstat, tix, info, tickets, verified) in con.execute("""
            select event_name, sport_name, level, watch_format, venue_name, city, lat, lon, location_precision,
                   start_date, end_date, date_status, ticket_info, info_url, tickets_url, verified_on
            from marts.mart_watch_events order by coalesce(start_date, date '2999-01-01'), event_name""").fetchall():
        events.append({"n": name, "sp": sport, "l": level, "f": fmt, "v": venue, "c": city, "y": round(float(lat), 5), "x": round(float(lon), 5),
                       "pr": prec or "", "s": str(start) if start else "", "e": str(end) if end else "", "d": dstat,
                       "t": tix or "", "u": info or "", "k": tickets or "", "vo": str(verified)})

    named = sum(1 for v in out_venues if v["q"] != "u")
    meta = {
        "generated": date.today().isoformat(),
        "venues": len(out_venues),
        "named": named,
        "confirmed": sum(1 for v in out_venues if v["q"] in ("c", "p")),
        "sports_total": len(sports),
        "sports_with_venues": sum(1 for s in sports if s["v"] > 0),
        "events": len(events),
        "link_outs": sum(len(v.get("ac", [])) for v in out_venues),
        "attribution": "Venue data: OpenStreetMap contributors (ODbL) and Overture Maps Foundation (CDLA-Permissive / Apache / CC0), plus hand-curated entries.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"meta": meta, "sports": sports, "venues": out_venues, "events": events}, ensure_ascii=False, separators=(",", ":")),
                   encoding="utf-8")
    size = OUT.stat().st_size / 1e6
    print(f"Wrote {OUT}: {len(out_venues):,} venues, {len(sports)} sports, {size:.2f} MB  (named {named:,}; confirmed {meta['confirmed']:,})")


if __name__ == "__main__":
    main()
