"""Read-only data tools for the chatbot prototype (docs/chatbot_plan.md, ADR 0033).

Every tool answers from app/data/venues.json only: no network, no model. Field codes are decoded here
(see the docstring of ingestion/export_app_data.py) so the model never has to guess what "q" or "f" mean.
"""
from __future__ import annotations

import json
import math
from datetime import date
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "app" / "data" / "venues.json"
PROFILE = Path(__file__).resolve().parent / "profile.json"  # stands in for the browser's localStorage

QUALITY = {"c": "confirmed name", "p": "business listing", "i": "name inferred from nearby park/school", "u": "unnamed"}
SOURCE = {"o": "OpenStreetMap", "p": "places directory", "b": "OpenStreetMap + places directory", "m": "hand-curated"}
CONFIRM = {"v": "confirmed in person", "o": "stated by the operator", "r": "reported, not independently confirmed"}
OFFER = {"O": "open play", "C": "clinics", "L": "private lessons", "G": "group classes", "D": "drop-in", "T": "tournaments",
         "E": "leagues", "S": "social events"}
SURFACE_BITS = {1: "indoor", 2: "outdoor", 4: "sand", 8: "clay", 16: "grass", 32: "hard", 64: "turf"}
ALIASES = {"pickle ball": "pickleball", "racket ball": "racquetball", "racketball": "racquetball"}

_data: dict | None = None


def data() -> dict:
    global _data
    if _data is None:
        _data = json.loads(DATA.read_text(encoding="utf-8"))
        _data["_by_id"] = {v["i"]: v for v in _data["venues"]}
    return _data


def _norm(s: str) -> str:
    return "".join(ch for ch in (s or "").lower() if ch.isalnum() or ch == " ").strip()


def _sport_index(name: str) -> tuple[int | None, list[str]]:
    """Resolve a user's sport word to an index in meta sports; second item = suggestions when unresolved."""
    sports = data()["sports"]
    q = ALIASES.get(_norm(name), _norm(name))
    for i, s in enumerate(sports):
        if _norm(s["n"]) == q:
            return i, []
    hits = [i for i, s in enumerate(sports) if q and (q in _norm(s["n"]) or _norm(s["n"]) in q)]
    if len(hits) == 1:
        return hits[0], []
    pool = hits or [i for i, s in enumerate(sports) if s["v"] > 0]
    return None, [sports[i]["n"] for i in pool][:12]


def _flags(f: int) -> dict:
    return {"lit": bool(f & 1), "public": bool(f & 2), "free": bool(f & 4), "members_only": bool(f & 8)}


def _bits(b: int) -> list[str]:
    return [label for bit, label in SURFACE_BITS.items() if b & bit]


def _km(a_lat, a_lon, b_lat, b_lon) -> float:
    p = math.pi / 180
    h = math.sin((b_lat - a_lat) * p / 2) ** 2 + math.cos(a_lat * p) * math.cos(b_lat * p) * math.sin((b_lon - a_lon) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))


def _city_center(city: str) -> tuple[float, float] | None:
    pts = [(v["y"], v["x"]) for v in data()["venues"] if _norm(v.get("c", "")) == _norm(city)]
    if not pts:
        return None
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def _access(f: int) -> str:
    return "members-only (marked private/members)" if f & 8 else "public" if f & 2 else "not stated"


def _sports_out(v: dict, sport_idx: int | None) -> list:
    """Queried sport in full; other sports on a shared court as names only (a tennis court fits many sheet sports)."""
    sports = data()["sports"]
    ps = [p for p in v.get("p", []) if p[2] != 128]  # flag 128 = wall sport inferred from a wall, not a court
    full = [{"sport": sports[p[0]]["n"], "courts": p[1] or "not stated", "surface": _bits(p[2]) or "not stated"}
            for p in ps if sport_idx is None or p[0] == sport_idx]
    others = [sports[p[0]]["n"] for p in ps if sport_idx is not None and p[0] != sport_idx]
    return full + ([{"also_listed_for": others[:6], "more": max(0, len(others) - 6)}] if others else [])


def _venue_out(v: dict, sport_idx: int | None = None, dist: float | None = None) -> dict:
    sports = data()["sports"]
    out = {
        "id": v["i"], "name": v["n"] or "(unnamed court)", "name_basis": QUALITY.get(v.get("q"), v.get("q")),
        "city": v.get("c") or None, "state": v.get("r"), "street_address": v.get("a") or None,
        "address_inferred": bool(v.get("ai")), "website": v.get("w") or None,
        "sports": _sports_out(v, sport_idx),
        "access": _access(v.get("f", 0)),
        "free": True if v.get("f", 0) & 4 else "not stated",
        "lit": True if v.get("f", 0) & 1 else "not stated",
        "public_access_not_confirmed": bool(v.get("xu")),
        "source": SOURCE.get(v.get("s"), v.get("s")),
        "offerings": [OFFER[c] for c in v.get("o", "") if c in OFFER],
    }
    if v.get("cf"):
        out["confirmation"] = CONFIRM.get(v["cf"], v["cf"]) + (f" ({v['cd']})" if v.get("cd") else "")
    if v.get("ru"):
        out["notes"] = v["ru"]
    if v.get("ac"):  # [type, title, url, provider, start, end, price]
        out["links"] = [{"type": a[0], "title": a[1], "url": a[2]} for a in v["ac"][:5]]
    if dist is not None:
        out["distance_km"] = round(dist, 1)
    return out


def search_venues(sport: str, city: str = "", near_city: str = "", radius_km: float = 25, state: str = "",
                  public_only: bool = False, free_only: bool = False, limit: int = 8) -> dict:
    idx, suggestions = _sport_index(sport)
    if idx is None:
        return {"error": f"Unknown sport '{sport}'.", "sports_with_venues": suggestions}
    center = None
    if near_city:
        center = _city_center(near_city)
        if center is None:
            return {"error": f"No venues known in '{near_city}', so no distance centre. Try city= instead."}
    rows = []
    for v in data()["venues"]:
        if v.get("kd") == "w" or not any(p[0] == idx and p[2] != 128 for p in v.get("p", [])):
            continue
        if state and v.get("r", "").lower() != state.lower():
            continue
        if city and _norm(city) not in _norm(v.get("c", "")):
            continue
        fl = _flags(v.get("f", 0))
        if public_only and not fl["public"]:
            continue
        if free_only and not fl["free"]:
            continue
        d = None
        if center:
            d = _km(center[0], center[1], v["y"], v["x"])
            if d > radius_km:
                continue
        rows.append((v, d))
    # confirmed names first, then distance (if any), then pins with a street address
    rows.sort(key=lambda r: (r[0].get("q") != "c", r[1] if r[1] is not None else 0, not r[0].get("a")))
    limit = max(1, min(int(limit), 15))
    shown = [_venue_out(v, idx, d) for v, d in rows[:limit]]
    counts = {}
    for o in shown:
        counts[o["name"]] = counts.get(o["name"], 0) + 1
    for o in shown:  # same name at different places (chain branches): tell them apart by street
        o["display_name"] = f'{o["name"]} ({o["street_address"] or o["city"] or "address not stated"})' if counts[o["name"]] > 1 else o["name"]
    return {"sport": data()["sports"][idx]["n"], "total_matches": len(rows), "shown": min(limit, len(rows)),
            "venues": shown,
            "note": "Only venues in our data (CA, NV, OR, WA, HI). Zero matches means none found here, not that none exist."}


def get_venue(venue_id: str) -> dict:
    v = data()["_by_id"].get(venue_id)
    return _venue_out(v) if v else {"error": f"No venue with id '{venue_id}'."}


def list_events(sport: str = "", city: str = "", include_past: bool = False) -> dict:
    today = date.today().isoformat()
    idx = None
    if sport:
        idx, suggestions = _sport_index(sport)
        if idx is None:
            return {"error": f"Unknown sport '{sport}'.", "sports_with_venues": suggestions}
    sname = data()["sports"][idx]["n"] if idx is not None else ""
    out = []
    for e in data()["events"]:
        if sname and e["sp"] != sname:
            continue
        if city and _norm(city) not in _norm(e.get("c", "")):
            continue
        if not include_past and (e.get("e") or e.get("s") or "9999") < today:
            continue
        out.append({"name": e["n"], "sport": e["sp"], "level": e["l"], "format": e["f"], "venue": e["v"], "city": e["c"],
                    "start": e["s"], "end": e["e"], "dates_status": e["d"], "tickets_info": e["t"], "info_link": e["u"],
                    "verified_on": e["vo"], "location_precision": e["pr"]})
    out.sort(key=lambda e: e["start"] or "9999")
    return {"today": today, "count": len(out), "events": out[:15],
            "note": "Events to WATCH (links out to the organizer). Empty means none listed in our data."}


def sport_info(sport: str) -> dict:
    idx, suggestions = _sport_index(sport)
    if idx is None:
        return {"error": f"Unknown sport '{sport}'.", "sports_with_venues": suggestions}
    s = data()["sports"][idx]
    return {"sport": s["n"], "description": s.get("d"), "facts": s.get("f"), "links": s.get("u"), "venues_in_our_data": s["v"],
            "note": "Description and facts come from our sport list. Anything beyond them is general knowledge: say so."}


def find_walls(sport: str = "", city: str = "", near_city: str = "", radius_km: float = 25, limit: int = 8) -> dict:
    center = _city_center(near_city) if near_city else None
    if near_city and center is None:
        return {"error": f"No venues known in '{near_city}', so no distance centre."}
    out = []
    for v in data()["venues"]:
        if v.get("kd") != "w":
            continue
        hw = v["hw"]
        if sport and not any(_norm(sport) in _norm(x) for x in hw.get("sp", [])):
            continue
        if city and _norm(city) not in _norm(v.get("c", "")):
            continue
        if center and _km(center[0], center[1], v["y"], v["x"]) > radius_km:
            continue
        out.append({"name": v["n"] or "Hitting wall", "city": v.get("c") or None, "state": v["r"], "wall_types": hw["t"], "sports": hw.get("sp", []),
                    "walls_at_pin": hw.get("wn", 1), "access": hw.get("ac"), "free": hw.get("f"), "lit": hw.get("l"), "confirmation": hw["cf"],
                    "evidence": hw["ev"], "reported_on": hw["d"], "lat": v["y"], "lon": v["x"]})
    return {"total_matches": len(out), "walls": out[:max(1, min(int(limit), 15))],
            "note": "Stand-alone wall pins only. Access 'yes'/'public'/'permissive' = public; unknown means not checked. Say when a wall is only tagged, not verified."}


def find_gear(sport: str = "", city: str = "") -> dict:
    return {"available": False,
            "message": "We have no gear-store or rental data yet (docs/chatbot_plan.md, step 3). Do not name stores from memory."}


def save_profile(sport: str = "", city: str = "", level: str = "") -> dict:
    cur = load_profile()
    for k, v in (("sport", sport), ("city", city), ("level", level)):
        if v:
            cur[k] = v
    PROFILE.write_text(json.dumps(cur), encoding="utf-8")
    return {"saved": cur, "where": "this browser only"}


def load_profile() -> dict:
    try:
        return json.loads(PROFILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


# JSON-schema definitions for the model
S = {"type": "string"}
TOOL_DEFS = [
    {"name": "search_venues", "description": "Find places to play a racket sport. Use city for a city/area name, or near_city + radius_km for nearby cities. Results are only what our data holds (CA, NV, OR, WA, HI).",
     "input_schema": {"type": "object", "properties": {"sport": S, "city": S, "near_city": S, "radius_km": {"type": "number"}, "state": {"type": "string", "enum": ["CA", "NV", "OR", "WA", "HI", ""]},
                                                       "public_only": {"type": "boolean"}, "free_only": {"type": "boolean"}, "limit": {"type": "integer"}}, "required": ["sport"]}},
    {"name": "get_venue", "description": "Full record for one venue id returned by search_venues.",
     "input_schema": {"type": "object", "properties": {"venue_id": S}, "required": ["venue_id"]}},
    {"name": "list_events", "description": "Upcoming events to watch (tournaments etc.), optionally by sport and city.",
     "input_schema": {"type": "object", "properties": {"sport": S, "city": S, "include_past": {"type": "boolean"}}}},
    {"name": "sport_info", "description": "How many venues we hold for a sport and its coverage status. No rules text.",
     "input_schema": {"type": "object", "properties": {"sport": S}, "required": ["sport"]}},
    {"name": "find_walls", "description": "Hitting walls / backboards for solo practice. Walls often have no city, so prefer near_city.",
     "input_schema": {"type": "object", "properties": {"sport": S, "city": S, "near_city": S, "radius_km": {"type": "number"}, "limit": {"type": "integer"}}}},
    {"name": "find_gear", "description": "Racket-sport gear stores and rentals, ranked. Currently has no data.",
     "input_schema": {"type": "object", "properties": {"sport": S, "city": S}}},
    {"name": "save_profile", "description": "Remember the user's main sport, city and skill level (stored in this browser only). Call only when the user states them.",
     "input_schema": {"type": "object", "properties": {"sport": S, "city": S, "level": S}}},
]
HANDLERS = {"search_venues": search_venues, "get_venue": get_venue, "list_events": list_events, "sport_info": sport_info,
            "find_walls": find_walls, "find_gear": find_gear, "save_profile": save_profile}


def call(name: str, args: dict) -> dict:
    try:
        return HANDLERS[name](**args)
    except KeyError:
        return {"error": f"Unknown tool {name}"}
    except TypeError as e:
        return {"error": f"Bad arguments: {e}"}
