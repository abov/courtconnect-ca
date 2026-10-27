"""Export the venue finder to a compact JSON file for the static map app (app/data/venues.json).

    python ingestion/export_app_data.py            (or: make app-data)

Deliberately NOT exported: phone numbers (some belong to individual instructors), Google IDs, and raw record ids.
Websites are exported only when `website_usable` is set, so dead links never reach the page.

File shape (kept small on purpose; ~2 MB for ~10,000 venues):
  meta    : counts, generation date, attribution
  sports  : [{n: name, v: venues, s: status, r: recommended next source, d blurb, f facts {p players, c court, g gear, o governing body, y year, ou official site},
              u links {l learn more, r rules, c court size, g gear} (https only)}], ordered by venues found
  venues  : [{i, n, q, s, y, x, c, r, a, w, o, f, p:[[sportIndex, courts, flagMask], ...], ac, ru, xu}]
     a street address; ai 1 + ad metres = nearest address point (inferred); ap 1 = address of the enclosing park/school/club (inferred); ns = nearest road name when no address (shown "Near <street>", inferred)
     r region CA/NV (ADR 0014); ac link-outs [type,title,url,provider,start,end,price]; ru notes (hand-curated); xu 1 = public access not confirmed; cf v/o/r confirmation; cd date; cn number of different people who confirmed it; up 'Opening soon' = confirmed but not open yet, or 'Reported: opening soon' with ul 1 = only a directory said so (ud = date checked)
     wl hitting walls on site (int_wall_venue_link): [[wall types joined by ';', walls at this venue, confirmation tagged/inferred/reported/official], ...], only on venues with a
        wall pin at them; a pointer to the walls layer, never counted as courts or in sport totals (tagged = from OpenStreetMap tags, not checked)
  events  : [{n name, sp sport, l level, f watch format, v venue, c city, y, x, pr location precision, s start, e end, d date status,
              t ticket info, u info link, k tickets link, vo verified on}]   (events to WATCH; every one links out to the organizer)
  social  : [{n series name, sp sport, k kind, o organizer, v venue, c city, y, x, pr location precision, sc schedule (organizer's wording), ll last listed date, sl skill level,
              au audience women/men/mixed, ag age focus, ct courts at the venue, pi price info, sk how it was found, u info link, g signup link, vo verified on}]   (recurring social get-togethers;
              every one links out to the organizer; au/ag are only what the organizer states, absent = not stated)
  walls   : [{n name, c city, r region, y, x, pr location precision, t [wall types], sp [sports suited], nv near venue, su surface, l lit 1/0 (absent = unknown),
              f free 1/0 (absent = unknown), ac access, cf confirmation, d reported on, ev evidence, wn walls at this pin (absent = 1)}]   (hitting walls for solo practice)
  platforms : [{n name, sp [sport indexes], d what it does, p price note, u https link, vo verified on}]   (player-matching apps, link-outs only)
     q name quality: c confirmed (court/operator name or hand-curated), p business listing, i inferred from nearby park/school, u unnamed
                (q i names shared in a city carry a computed "(north courts, 6 courts)" suffix: position + court count, not a source)
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


def https_only(url: str) -> str:
    url = (url or "").strip()
    if url and not url.startswith("https://"):
        raise SystemExit(f"Sport link must be https: {url!r} (fix it in the Google Sheet, then make sync-sports)")
    return url


def add_sport_details(con, sports: list, sport_index: dict) -> None:
    """Mini description for the sport card: blurb + facts + rules/court/gear links, all from the Google Sheet via the all_racquet seed.
    The link/blurb columns may not exist yet (sheet not extended): then only the facts are exported."""
    have = {r[0] for r in con.execute("select column_name from information_schema.columns where table_schema = 'raw' and table_name = 'all_racquet'").fetchall()}
    col = lambda c: f"trim(cast({c} as varchar))" if c in have else "''"   # cast: an all-blank sheet column loads as INTEGER
    for row in con.execute(f"""select trim(sport), {col('players')}, {col('court_dim')}, {col('base_gear')}, {col('org')}, {col('year_origin')},
                               {col('url')}, {col('blurb')}, {col('learn_url')}, {col('rules_url')}, {col('court_url')}, {col('gear_url')}
                        from raw.all_racquet""").fetchall():
        name, players, court, gear, org, year, official, blurb, learn, rules, court_url, gear_url = (v or "" for v in row)
        if name not in sport_index:
            continue
        if len(blurb) > 200:
            raise SystemExit(f"Blurb for {name} is {len(blurb)} characters (max 200): shorten it in the Google Sheet")
        facts = {k: v for k, v in (("p", players), ("c", court), ("g", gear), ("o", org), ("y", year), ("ou", https_only(official))) if v}
        links = {k: https_only(v) for k, v in (("l", learn), ("r", rules), ("c", court_url), ("g", gear_url)) if v}
        entry = sports[sport_index[name]]
        if blurb:
            entry["d"] = blurb
        if facts:
            entry["f"] = facts
        if links:
            entry["u"] = links


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    con = duckdb.connect("courtconnect.duckdb", read_only=True)

    gaps = con.execute("""
        select g.sport_name, g.coverage_status, g.venues_found, g.recommended_next_source
        from marts.mart_sport_gaps g order by g.venues_found desc, g.sport_name""").fetchall()
    sport_index = {r[0]: i for i, r in enumerate(gaps)}
    sports = [{"n": r[0], "v": int(r[2]), "s": r[1], "r": r[3]} for r in gaps]
    add_sport_details(con, sports, sport_index)
    # sports that need no fixed court (any beach): w = where, wn = note; the map lists them without pinpointing a place
    for name, where, note in con.execute("select trim(sport), trim(where_played), trim(note) from raw.sport_play_anywhere").fetchall():
        if name in sport_index:
            sports[sport_index[name]].update({"w": where, "wn": note})

    # sports played on another sport's courts: b = indexes of the court sports they share (the panel groups them, not counts them again)
    # st = same equipment, equally valid (Teqis on a Teqpong table): the popup lists it next to the base sport, not as an optional note
    for name, base, same in con.execute("select trim(also_sport), trim(sport), lower(trim(coalesce(same_table, ''))) from raw.sport_also_played").fetchall():
        if name in sport_index and base in sport_index:
            sports[sport_index[name]].setdefault("b", []).append(sport_index[base])
            if same == "yes":
                sports[sport_index[name]]["st"] = 1

    rows = con.execute("""
        select venue_id, venue_name, name_source, venue_source, sport_name, courts_for_sport, lat, lon, city, region, address_line,
               website_usable, offerings, address_source, address_distance_m, has_indoor, has_outdoor, has_sand_beach, has_clay, has_grass, has_hard, has_turf,
               has_lit_courts, is_confirmed_public, has_free_courts, is_members_only, also_listed_as, near_street
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

    # Venues confirmed but not open yet (venue_opening_status.csv): shown with a hollow pin and an "Opening soon" badge. Merged venues included.
    opening = {vid: (status, ev, str(vo)) for vid, status, ev, vo in con.execute("""
            select mm.effective_venue_id, s.opening_status, s.evidence, s.verified_on
            from raw.venue_opening_status s join intermediate.int_manual_venue_match mm on mm.venue_key = trim(s.venue_key)""").fetchall()}

    # How many different people confirmed (visited / official) and how many only reported (word of mouth) each hand-added venue
    # (venue_confirmations.csv; handles only, never shown). Someone who also confirmed is not counted again as a reporter.
    confirmers: dict[str, int] = {}
    reporters: dict[str, int] = {}
    for vid, nconf, nrep in con.execute("""
            with people as (
                select mm.effective_venue_id as vid, c.confirmed_by, max(case when c.method <> 'reported' then 1 else 0 end) as confirmed
                from staging.stg_venue_confirmations c join intermediate.int_manual_venue_match mm on mm.venue_key = c.venue_key
                group by 1, 2)
            select vid, sum(confirmed), sum(1 - confirmed) from people group by 1""").fetchall():
        if nconf:
            confirmers[vid] = int(nconf)
        if nrep:
            reporters[vid] = int(nrep)

    venues: dict[str, dict] = {}
    entries: dict[str, list] = defaultdict(list)
    for (vid, name, nsrc, vsrc, sport, courts, lat, lon, city, region, addr, web, offers, asrc, adist, indoor, outdoor, sand, clay, grass, hard, turf,
         lit, public, free, members, also, near) in rows:
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
                "c": (city.title() if city and city.isupper() else city) or "",   # county point data gives ALL CAPS cities
                "r": region,
                "a": (addr.title() if addr and asrc == "overture_nearest" and addr.isupper() else addr) or "",   # county point data is often ALL CAPS
                "w": web or "",
                "o": "".join(OFFER_CODES[o] for o in (offers or "").split(";") if o in OFFER_CODES),
                "f": (1 if lit else 0) | (2 if public else 0) | (4 if free else 0) | (8 if members else 0),
            }
            if asrc in ("overture_nearest", "nominatim"):   # inferred: nearest Overture address point or cached Nominatim lookup, shown as "Nearest address (inferred)"
                venues[vid]["ai"] = 1
                venues[vid]["ad"] = int(adist)   # metres from the pin
            if asrc == "osm_parent":   # address mapped on the enclosing park / school / club (inferred for these courts)
                venues[vid]["ap"] = 1
            if near and not addr:      # no address, but a named road: shown as "Near <street>", inferred
                venues[vid]["ns"] = near
            if also:
                venues[vid]["al"] = also   # other listed names at the same address (merged duplicates)
        mask = sum(bit for flag, bit in ((indoor, 1), (outdoor, 2), (sand, 4), (clay, 8), (grass, 16), (hard, 32), (turf, 64)) if flag)
        entries[vid].append([sport_index[sport], int(courts or 0), mask])
        venues[vid]["_o"] = venues[vid].get("_o", set()) | {c for c in (venues[vid]["o"] or "")}

    # Walls standing at a listed venue (int_wall_venue_link): shown in that venue's popup as "Hitting walls on site", grouped by wall type and confirmation.
    # A pointer only: walls are not courts, so nothing here touches `p` or the sport and venue counts.
    wall_links: dict[str, dict] = defaultdict(dict)
    for vid, wtype, conf, count in con.execute("""
            select l.venue_id, w.wall_type, w.confirmation, w.wall_count
            from intermediate.int_wall_venue_link l join marts.mart_wall_pins w on w.wall_key = l.wall_key
            order by l.venue_id, w.wall_type, w.confirmation""").fetchall():
        key = (wtype, conf)
        wall_links[vid][key] = wall_links[vid].get(key, 0) + int(count)

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
            if reporters.get(vid):
                v["rn"] = reporters[vid]        # number of different people who reported it (word of mouth, not confirmed)
            if manual[vid]["u"]:
                v["xu"] = 1                      # public access not confirmed on the source map
        if vid in wall_links:
            v["wl"] = [[t, n, c] for (t, c), n in wall_links[vid].items()]   # hitting walls on site: [wall types, walls, confirmation]
        if vid in opening:
            v["up"] = opening[vid][0]            # not open yet: the badge text; the popup adds the caveat
            v["ud"] = opening[vid][2]            # date the page was read
            if opening[vid][0].startswith("Reported"):
                v["ul"] = 1                      # only a directory / press listing says it is coming: lighter pin, softer caveat
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

    # Social get-togethers: recurring series (not dates), link-out only. Audience and age focus are organizer-stated; absent keys mean "not stated", never a guess (ADR 0021).
    social = []
    for (name, sport, kind, org, venue, city, lat, lon, prec, sched, last, skill, aud, age, courts, price, skind, info, signup, verified) in con.execute("""
            select series_name, sport_name, kind, organizer, venue_name, city, lat, lon, location_precision, schedule, last_listed_date, skill_level,
                   audience, age_focus, courts, price_info, source_kind, info_url, signup_url, verified_on
            from marts.mart_social_events order by sport_name, city, series_name""").fetchall():
        e = {"n": name, "sp": sport, "k": kind, "o": org, "v": venue, "c": city, "y": round(float(lat), 5), "x": round(float(lon), 5), "pr": prec or "",
             "sc": sched, "sk": skind, "vo": str(verified)}
        for key, val in (("ll", str(last) if last else ""), ("sl", skill), ("au", aud), ("ag", age), ("ct", courts), ("pi", price), ("u", info), ("g", signup)):
            if val: e[key] = val
        social.append(e)

    # Hitting walls: solo practice, one row per map pin (walls side by side share a pin, wn = how many). Unknown lit / free flags are left out of the row, never exported as 0.
    walls = []
    for (name, city, region, lat, lon, prec, wtype, suited, near, surf, lit, free, access, conf, rep, evid, count) in con.execute("""
            select wall_name, city, region, lat, lon, location_precision, wall_type, sports_suited, near_venue_name, surface, is_lit, free_to_use,
                   access, confirmation, reported_on, evidence, wall_count
            from marts.mart_wall_pins order by city, wall_name, wall_key""").fetchall():
        w = {"n": name, "c": city, "r": region, "y": round(float(lat), 5), "x": round(float(lon), 5), "pr": prec or "", "t": [x.strip() for x in wtype.split(";") if x.strip()],
             "sp": [x.strip() for x in (suited or "").split(";") if x.strip()], "cf": conf, "d": str(rep), "ev": evid or ""}
        if near: w["nv"] = near
        if surf: w["su"] = surf
        if lit is not None: w["l"] = 1 if lit else 0
        if free is not None: w["f"] = 1 if free else 0
        if access: w["ac"] = access
        if count > 1: w["wn"] = int(count)
        walls.append(w)

    # Player-matching apps (social phase A): link-outs shown under "Find people to play with". Sports are indexes into `sports`.
    platforms = []
    for name, sps, what, price, url, verified in con.execute(
            "select trim(platform), trim(sports), trim(what), trim(price_note), trim(url), trim(verified_on) from raw.player_platforms order by platform").fetchall():
        platforms.append({"n": name, "sp": [sport_index[s.strip()] for s in sps.split(";") if s.strip() in sport_index], "d": what, "p": price,
                          "u": https_only(url), "vo": verified})

    named = sum(1 for v in out_venues if v["q"] != "u")
    meta = {
        "generated": date.today().isoformat(),
        "venues": len(out_venues),
        "named": named,
        "confirmed": sum(1 for v in out_venues if v["q"] in ("c", "p")),
        "sports_total": len(sports),
        "sports_with_venues": sum(1 for s in sports if s["v"] > 0),
        "events": len(events),
        "social": len(social),
        "walls": sum(w.get("wn", 1) for w in walls),
        "link_outs": sum(len(v.get("ac", [])) for v in out_venues),
        "attribution": "Venue data: OpenStreetMap contributors (ODbL) and Overture Maps Foundation (CDLA-Permissive / Apache / CC0), plus hand-curated entries.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"meta": meta, "sports": sports, "venues": out_venues, "events": events, "social": social, "walls": walls, "platforms": platforms}, ensure_ascii=False, separators=(",", ":")),
                   encoding="utf-8")
    size = OUT.stat().st_size / 1e6
    print(f"Wrote {OUT}: {len(out_venues):,} venues, {len(sports)} sports, {size:.2f} MB  (named {named:,}; confirmed {meta['confirmed']:,})")


if __name__ == "__main__":
    main()
