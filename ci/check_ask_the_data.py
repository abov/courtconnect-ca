"""Check that the SQL behind app/ask-the-data.html still runs against app/data/venues.json.
The page runs app/ask-the-data-queries.json in the browser (DuckDB-WASM); this runs the same text with Python DuckDB, so a renamed or
dropped export key fails here instead of on the live page. Also checks the numbers it can: tables match meta counts, no question returns
nothing, and the vendored engine files match app/vendor/duckdb/SHA256SUMS. Offline.
Run: python ci/check_ask_the_data.py"""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
VENUES = APP / "data" / "venues.json"
spec = json.loads((APP / "ask-the-data-queries.json").read_text(encoding="utf-8"))
meta = json.loads(VENUES.read_text(encoding="utf-8"))["meta"]
problems = []

con = duckdb.connect()
for sql in spec["setup"]:
    con.execute(sql.replace("{{FILE}}", VENUES.as_posix()))

n_venues = con.execute("SELECT count(*) FROM venues").fetchone()[0]
if n_venues != meta["venues"]:
    problems.append(f"venues table has {n_venues} rows, meta says {meta['venues']}")
n_sports = con.execute("SELECT count(*) FROM sports").fetchone()[0]
if n_sports != meta["sports_total"]:
    problems.append(f"sports table has {n_sports} rows, meta says {meta['sports_total']}")
with_venues = con.execute("SELECT count(DISTINCT sport_id) FROM venue_sports").fetchone()[0]
if with_venues != meta["sports_with_venues"]:
    problems.append(f"{with_venues} sports have venues, meta says {meta['sports_with_venues']}")
orphans = con.execute("SELECT count(*) FROM venue_sports WHERE sport_id NOT IN (SELECT sport_id FROM sports)").fetchone()[0]
if orphans:
    problems.append(f"{orphans} venue_sports rows point at a sport id that does not exist")

for q in spec["questions"]:
    try:
        rows = con.execute(q["sql"]).fetchall()
    except Exception as e:  # noqa: BLE001 - report which question broke
        problems.append(f"question {q['title']!r} failed: {e}")
        continue
    if not rows:
        problems.append(f"question {q['title']!r} returned no rows")

# plain-English box (app/ask-the-data-nl.js): each test question must give SQL that runs and returns rows, or be declined.
# It needs node (preinstalled on GitHub runners); the template logic lives in JS, so this is the only way to run it offline.
nl_cases = 0
if shutil.which("node") is None:
    print("note: node not found, plain-English questions not checked")
else:
    proc = subprocess.run(["node", str(ROOT / "chatbot" / "dump_ask_the_data.js")], capture_output=True, text=True, encoding="utf-8")
    if proc.returncode != 0:
        problems.append("chatbot/dump_ask_the_data.js failed: " + proc.stderr.strip()[:300])
    else:
        cases = {c["question"]: c for c in json.loads((APP / "ask-the-data-questions.json").read_text(encoding="utf-8"))["cases"]}
        for r in json.loads(proc.stdout):
            res, c = r["result"], cases[r["question"]]
            nl_cases += 1
            if c["expect"] == "no":
                if res["ok"]:
                    problems.append(f"plain question {r['question']!r} should be declined but gave SQL")
                continue
            if not res["ok"]:
                problems.append(f"plain question {r['question']!r} was declined: {res['message'][:80]}")
                continue
            for word in c.get("contains", []):
                if word.lower() not in res["title"].lower():
                    problems.append(f"plain question {r['question']!r}: title {res['title']!r} lacks {word!r}")
            try:
                rows = con.execute(res["sql"]).fetchall()
            except Exception as e:  # noqa: BLE001
                problems.append(f"plain question {r['question']!r}: SQL failed: {e}")
                continue
            if not rows and not c.get("may_be_empty"):
                problems.append(f"plain question {r['question']!r} returned no rows")

# the tables the page lists must exist, and each column named first in a description must be a real column
for table, desc in spec["tables"].items():
    cols = {r[0] for r in con.execute(f"DESCRIBE {table}").fetchall()}
    if table == "venue_sport_names":
        continue  # a view described in prose
    listed = set()
    depth = 0
    for part in desc.split(","):
        name = part.strip().split(" ")[0]
        if depth == 0 and name:
            listed.add(name)
        depth += part.count("(") - part.count(")")
    missing = listed - cols
    if missing:
        problems.append(f"table {table} description names columns that do not exist: {sorted(missing)}")

# vendored engine files match their recorded checksums
sums = APP / "vendor" / "duckdb" / "SHA256SUMS"
if not sums.exists():
    problems.append("app/vendor/duckdb/SHA256SUMS is missing")
else:
    for line in sums.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split(None, 1)
        f = sums.parent / name.strip().lstrip("*")
        if not f.exists():
            problems.append(f"vendored file {f.name} is missing")
        elif hashlib.sha256(f.read_bytes()).hexdigest() != digest:
            problems.append(f"vendored file {f.name} does not match SHA256SUMS")

if problems:
    print("ask-the-data check FAILED:")
    for p in problems:
        print(" -", p)
    sys.exit(1)
print(f"ask-the-data: {len(spec['setup'])} setup statements and {len(spec['questions'])} questions and {nl_cases} plain-English questions run on {n_venues:,} venues; tables match meta; vendored files match SHA256SUMS")
