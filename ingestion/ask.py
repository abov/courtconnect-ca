"""Ask a plain-English question about the market marts; answers come from vetted, parameterised queries only.

    python ingestion/ask.py "where could a padel club open? no padel nearby"      (needs Ollama running locally)
    python ingestion/ask.py --template sport_gaps sport=Padel min_racket_venues=30  (no model needed)
    python ingestion/ask.py --list

A free local model (Ollama, http://localhost:11434) only PICKS one of the templates below and fills its parameters as JSON. It never writes SQL:
a small model can return a confident wrong number, and these figures are inferred. DuckDB runs the chosen template on a read-only connection to
courtconnect.duckdb, and the SQL, the caveat and the sport list check are always shown. Nothing leaves your machine. See docs/market_insights.md.
Model: env OLLAMA_MODEL (default qwen2.5:3b).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

import duckdb

DB = "courtconnect.duckdb"
SNAPSHOTS = Path(__file__).resolve().parent.parent / "docs" / "market_snapshots.csv"
OLLAMA_URL = "http://localhost:11434/api/generate"
CAVEAT = "Inferred from known venues only (private clubs undercounted), straight-line miles, no population data. A gap can mean missing data."

# name -> description, params {name: (type, required, default)}, sql (named $params; every optional one is null-safe)
TEMPLATES: dict[str, dict] = {
    "sport_gaps": {
        "desc": "Cities with plenty of racket activity but no known venue for a sport within 15 miles (where could it open / where is it missing).",
        "params": {"sport": (str, True, None), "min_racket_venues": (int, False, 20), "region": (str, False, None)},
        "sql": """
            select region, city, racket_venues_in_city, nearest_mi, sport_coverage_status
            from marts.mart_market_gaps
            where lower(sport_name) = lower($sport) and gap_status = 'no_venue_within_15mi'
              and racket_venues_in_city >= $min_racket_venues and ($region is null or region = upper($region))
            order by racket_venues_in_city desc limit 25""",
    },
    "city_sports": {
        "desc": "Which racket sports a city has, how many venues and courts, and what is available within 15 miles.",
        "params": {"city": (str, True, None), "region": (str, False, None)},
        "sql": """
            select sport_name, venues_in_city, courts_in_city, public_venues_in_city, venues_within_15mi, nearest_mi, gap_status
            from marts.mart_market_gaps
            where upper(city) = upper($city) and ($region is null or region = upper($region))
              and (venues_in_city > 0 or venues_within_15mi > 0)
            order by venues_in_city desc, venues_within_15mi desc limit 25""",
    },
    "venue_competition": {
        "desc": "How many other venues offer the same sport within 5 and 15 miles of a named venue or club (its local competition).",
        "params": {"venue": (str, True, None), "sport": (str, False, None)},
        "sql": """
            select venue_name, city, sport_name, same_sport_venues_5mi, same_sport_venues_15mi, nearest_same_sport_mi
            from marts.mart_venue_neighbors
            where venue_name ilike '%' || $venue || '%' and ($sport is null or lower(sport_name) = lower($sport))
            order by same_sport_venues_15mi desc limit 25""",
    },
    "nearby_sports": {
        "desc": "Other racket sports within 15 miles of a named venue that the venue does not list (try a new sport near here).",
        "params": {"venue": (str, True, None)},
        "sql": """
            select v.venue_name, v.city, s.sport_name, s.venues_within_5mi, s.venues_within_15mi, s.nearest_mi
            from marts.mart_venue_nearby_sports s
            join (select distinct venue_id, venue_name, city from marts.mart_venue_finder) v on v.venue_id = s.venue_id
            where v.venue_name ilike '%' || $venue || '%'
            order by v.venue_name, s.nearest_mi limit 25""",
    },
    "trend": {
        "desc": "Venue count over time for a sport, statewide or for one city, from the refresh snapshots (needs 2+ snapshots to show a trend).",
        "params": {"sport": (str, True, None), "city": (str, False, None)},
        "sql": f"""
            select date, sum(venues) as venues, sum(courts) as courts
            from read_csv('{SNAPSHOTS.as_posix()}')
            where lower(sport_name) = lower($sport) and ($city is null or upper(city) = upper($city))
            group by date order by date""",
    },
}


def describe() -> str:
    lines = []
    for name, t in TEMPLATES.items():
        ps = ", ".join(f"{p}{'' if req else '?'}:{typ.__name__}" for p, (typ, req, _) in t["params"].items())
        lines.append(f"- {name}({ps}): {t['desc']}")
    return "\n".join(lines)


def route_with_model(question: str, model: str) -> dict:
    """Ask the local model to choose a template. Returns {'template': str, 'params': {...}}; raises on any problem."""
    prompt = (
        "You route questions about racket-sport venues to ONE query template. Reply with JSON only: "
        '{"template": "<name>", "params": {"<param>": <value>}}. Use only the templates and parameters listed; '
        "omit optional parameters you do not need; sport names are plain English like Padel, Pickleball, Tennis, Squash. "
        'If no template fits, reply {"template": "none", "params": {}}.\n\nTemplates:\n' + describe() + f"\n\nQuestion: {question}\nJSON:"
    )
    body = json.dumps({"model": model, "prompt": prompt, "format": "json", "stream": False, "options": {"temperature": 0}}).encode()
    req = urllib.request.Request(OLLAMA_URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(json.loads(r.read())["response"])


def validate(template: str, raw: dict, sports: list[str]) -> dict:
    """Check the chosen template and parameters; return the full parameter dict for the query. Raises ValueError with a readable reason."""
    if template not in TEMPLATES:
        raise ValueError(f"No template fits that question. Available:\n{describe()}")
    spec = TEMPLATES[template]["params"]
    extra = set(raw) - set(spec)
    if extra:
        raise ValueError(f"Unknown parameter(s) for {template}: {', '.join(sorted(extra))}")
    out: dict = {}
    for name, (typ, required, default) in spec.items():
        val = raw.get(name)
        if val in (None, ""):
            if required:
                raise ValueError(f"{template} needs '{name}'.")
            out[name] = default
            continue
        try:
            out[name] = typ(val)
        except (TypeError, ValueError):
            raise ValueError(f"'{name}' must be {typ.__name__}, got {val!r}.") from None
    if out.get("sport"):
        match = [s for s in sports if s.lower() == out["sport"].lower()]
        if not match:
            close = [s for s in sports if out["sport"].lower() in s.lower()][:5]
            raise ValueError(f"Unknown sport '{out['sport']}'." + (f" Did you mean: {', '.join(close)}?" if close else ""))
        out["sport"] = match[0]
    if out.get("region") and out["region"].upper() not in ("CA", "NV"):
        raise ValueError("region must be CA or NV.")
    return out


def run(con: duckdb.DuckDBPyConnection, template: str, params: dict) -> tuple[list[str], list[tuple]]:
    cur = con.execute(TEMPLATES[template]["sql"], params)
    return [d[0] for d in cur.description], cur.fetchall()


def show(cols: list[str], rows: list[tuple]) -> None:
    if not rows:
        print("(no rows: nothing matched, or nothing within range in our data)")
        return
    w = [max(len(str(c)), *(len(str(r[i])) for r in rows)) for i, c in enumerate(cols)]
    print("  ".join(str(c).ljust(w[i]) for i, c in enumerate(cols)))
    for r in rows:
        print("  ".join(str(v).ljust(w[i]) for i, v in enumerate(r)))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("question", nargs="*", help="plain-English question (routed by a local Ollama model), or key=value pairs with --template")
    ap.add_argument("--template", choices=list(TEMPLATES), help="skip the model and run this template; pass parameters as key=value")
    ap.add_argument("--list", action="store_true", help="list the templates and exit")
    ap.add_argument("--model", default=os.environ.get("OLLAMA_MODEL", "qwen2.5:3b"))
    a = ap.parse_args()
    if a.list:
        print(describe())
        return
    if not a.question and not a.template:
        ap.error("give a question, or --template NAME key=value ...")

    con = duckdb.connect(DB, read_only=True)
    sports = [r[0] for r in con.execute("select distinct sport_name from marts.mart_market_gaps").fetchall()]
    try:
        if a.template:
            template, raw = a.template, dict(kv.split("=", 1) for kv in a.question)
        else:
            try:
                choice = route_with_model(" ".join(a.question), a.model)
            except OSError as e:
                sys.exit(f"Could not reach Ollama at {OLLAMA_URL} ({e}). Start it (ollama serve; ollama pull {a.model}) or use --template.")
            template, raw = str(choice.get("template", "none")), dict(choice.get("params") or {})
        params = validate(template, raw, sports)
    except ValueError as e:
        sys.exit(str(e))

    print(f"Template: {template}  Parameters: {params}")
    print("SQL:" + " ".join(TEMPLATES[template]["sql"].split()).join(["\n  ", ""]))
    print()
    show(*run(con, template, params))
    print(f"\n{CAVEAT}")


if __name__ == "__main__":
    main()
