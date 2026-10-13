"""Export the venue finder to a compact JSON file for the static map app (app/data/venues.json).

    python ingestion/export_app_data.py            (or: make app-data)

Deliberately NOT exported: phone numbers (some belong to individual instructors), Google IDs, and raw record ids.
Websites are exported only when `website_usable` is set, so dead links never reach the page.

File shape (kept small on purpose; ~2 MB for ~10,000 venues):
  meta    : counts, generation date, attribution
  sports  : [{n: name, v: venues, s: status, r: recommended next source}], ordered by venues found
  venues  : [{i, n, q, s, y, x, c, a, w, o, f, p:[[sportIndex, courts, flagMask], ...], ac, ru, xu}]
     ac link-outs [type,title,url,provider,start,end,price]; ru notes (hand-curated); xu 1 = public access not confirmed; cf v/o/r confirmation; cd date; cn number of different people who confirmed it
  events  : [{n name, sp sport, l level, f watch format, v venue, c city, y, x, pr location precision, s start, e end, d date status,
              t ticket info, u info link, k tickets link, vo verified on}]   (events to WATCH; every one links out to the organizer)
  walls   : [{n name, c city, y, x, pr location precision, t [wall types], sp [sports suited], nv near venue, su surface, l lit 1/0 (absent = unknown),
              f free 1/0 (absent = unknown), ac access, cf confirmation, d reported on, ev evidence}]   (hitting walls for solo practice)
     q name quality: c confirmed (court/operator name or hand-curated), p business listing, i inferred from nearby park/school, u unnamed
     s source: o OpenStreetMap, p places, b both, m hand-curated
     f venue bits: 1 lit, 2 public, 4 free, 8 members-only (marked private/members, not marked public)      p[i][2] sport bits: 1 indoor, 2 outdoor, 4 sand, 8 clay, 16 grass, 32 hard, 64 turf
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
    # sports that need no fixed court (any beach): w = where, wn = note; the map lists them without pinpointing a place
    for name, where, note in con.execute("select trim(sport), trim(where_played), trim(note) from raw.sport_play_anywhere").fetchall():
        if name in sport_index:
            sports[sport_index[name]].update({"w": where, "wn": note})

    # sports played on another sport's courts: b = indexes of the court sports they share (the panel groups them, not counts them again)
    for name, base in con.execute("select trim(also_sport), trim(sport) from raw.sport_also_played").fetchall():
        if name in sport_index and base in sport_index:
            sports[sport_index[name]].setdefault("b", []).append(sport_index[base])

    rows = con.execute("""
        select venue_id, venue_name, name_source, venue_source, sport_name, courts_for_sport, lat, lon, city, address_line,
               website_usable, offerings, has_indoor, has_outdoor, has_sand_beach, has_clay, has_grass, has_hard, has_turf,
               has_lit_courts, is_confirmed_public, has_free_courts, is_members_only
        from marts.mart_venue_finder""").fetchall()

    # Things to do at a venue: link-outs to the provider's own page (CourtConnect books nothing). Current ones only.
    actions: dict[str, list] = defaultdict(list)
    for vid, atype, title, provider, url, price, start, end in con.execute("""
            select venue_id, action_type, title, provider, url, price_info, start_date, end_date
            from marts.mart_venue_actions where is_current order by action_type, title""").fetchall():
        actions[vid].append([atype, title, url, provider, str(start) if start else "", str(end) if end else "", price or ""])
    ORDER = ["open_play", "drop_in", "group_class", "clinic", "private_lesson", "court_booking", "league", "tournament", "social_event", "club_page", "social"]
    for lst in actions.values():                       # show ways to PLAY first, then dated events soonest first, then the general club page
        lst.sort(key=lambda x: (ORDER.index(x[0]) if x[0] in ORDER else 99, x[4] or "9999", x[1]))

    # Notes from the hand-curated paddle tennis map: court rules, and whether public access is confirmed (merged venues included).
    manual = {}
    for vid, rules, unconfirmed, rank, cdate in con.execute("""
            select mm.effective_venue_id, min(case when lower(m.rules_note) <> 'unknown' then m.rules_note end),
                   max(case when m.access_type = 'unknown' then 1 else 0 end),
                   min(case m.confirmation_level when 'visited' then 1 when 'official' then 2 else 3 end),
                   max(m.confirmed_on)
            from staging.stg_manual_venues m join intermediate.int_manual_venue_match mm on mm.venue_key = m.venue_key
            group by 1""").fetchall():
        manual[vid] = {"r": rules or "", "u": int(unconfirmed), "cf": {1: "v", 2: "o", 3: "r"}[rank], "cd": str(cdate) if cdate else ""}

    # How many different people confirmed each hand-added venue (venue_confirmations.csv; handles only, never shown).
    confirmers: dict[str, int] = {}
    for vid, n in con.execute("""
            select mm.effective_venue_id, count(distinct c.confirmed_by)
            from staging.stg_venue_confirmations c join intermediate.int_manual_venue_match mm on mm.venue_key = c.venue_key
            group by 1""").fetchall():
        confirmers[vid] = int(n)

    venues: dict[str, dict] = {}
    entries: dict[str, list] = defaultdict(list)
    for (vid, name, nsrc, vsrc, sport, courts, lat, lon, city, addr, web, offers, indoor, outdoor, sand, clay, grass, hard, turf,
         lit, public, free, members) in rows:
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
                "f": (1 if lit else 0) | (2 if public else 0) | (4 if free else 0) | (8 if members else 0),
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
            v["cf"] = manual[vid]["cf"]          # confirmation: v visited in person, o stated by the operator, r reported only
            if manual[vid]["cf"] == "v" and manual[vid]["cd"]:
                v["cd"] = manual[vid]["cd"]
            if confirmers.get(vid):
                v["cn"] = confirmers[vid]       # number of different people who confirmed it
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

    # Hitting walls: solo practice. Unknown lit / free flags are left out of the row, never exported as 0.
    walls = []
    for (name, city, lat, lon, prec, wtype, suited, near, surf, lit, free, access, conf, rep, evid) in con.execute("""
            select wall_name, city, lat, lon, location_precision, wall_type, sports_suited, near_venue_name, surface, is_lit, free_to_use,
                   access, confirmation, reported_on, evidence
            from core.dim_wall order by city, wall_name""").fetchall():
        w = {"n": name, "c": city, "y": round(float(lat), 5), "x": round(float(lon), 5), "pr": prec or "", "t": [x.strip() for x in wtype.split(";") if x.strip()],
             "sp": [x.strip() for x in (suited or "").split(";") if x.strip()], "cf": conf, "d": str(rep), "ev": evid or ""}
        if near: w["nv"] = near
        if surf: w["su"] = surf
        if lit is not None: w["l"] = 1 if lit else 0
        if free is not None: w["f"] = 1 if free else 0
        if access: w["ac"] = access
        walls.append(w)

    named = sum(1 for v in out_venues if v["q"] != "u")
    meta = {
        "generated": date.today().isoformat(),
        "venues": len(out_venues),
        "named": named,
        "confirmed": sum(1 for v in out_venues if v["q"] in ("c", "p")),
        "sports_total": len(sports),
        "sports_with_venues": sum(1 for s in sports if s["v"] > 0),
        "events": len(events),
        "walls": len(walls),
        "link_outs": sum(len(v.get("ac", [])) for v in out_venues),
        "attribution": "Venue data: OpenStreetMap contributors (ODbL) and Overture Maps Foundation (CDLA-Permissive / Apache / CC0), plus hand-curated entries.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"meta": meta, "sports": sports, "venues": out_venues, "events": events, "walls": walls}, ensure_ascii=False, separators=(",", ":")),
                   encoding="utf-8")
    size = OUT.stat().st_size / 1e6
    print(f"Wrote {OUT}: {len(out_venues):,} venues, {len(sports)} sports, {size:.2f} MB  (named {named:,}; confirmed {meta['confirmed']:,})")


if __name__ == "__main__":
    main()
