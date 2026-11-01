"""Fail when the committed app/data/venues.json is stale relative to the seeds.

CI only has a small fixture dataset, so it cannot regenerate the full export. Instead this checks what the seeds promise:
every `also_sport` in sport_also_played.csv must be listed with venues, and every watch event that has not ended by the
export date must be present. If it fails: `make app-data` (or run ingestion/export_app_data.py) after a full build, commit venues.json.
"""
import csv
import json
import sys
from pathlib import Path

seeds = Path("transform/seeds")
data = json.loads(Path("app/data/venues.json").read_text(encoding="utf-8"))
generated = data["meta"]["generated"]
problems = []

venues_by_sport = {s["n"]: s["v"] for s in data["sports"]}
with open(seeds / "sport_also_played.csv", encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f):
        if venues_by_sport.get(row["also_sport"], 0) == 0:
            problems.append(f"{row['also_sport']} (also played on {row['sport']} courts) has no venues in venues.json")

with open(seeds / "watch_events.csv", encoding="utf-8", newline="") as f:
    expected = {r["event_name"] for r in csv.DictReader(f) if (r["end_date"] or r["start_date"]) >= generated}
exported = {e["n"] for e in data["events"]}
for name in sorted(expected - exported):
    problems.append(f"watch event missing from venues.json: {name}")

with open(seeds / "social_events.csv", encoding="utf-8", newline="") as f:
    expected_social = {r["series_name"] for r in csv.DictReader(f) if (r["last_listed_date"] or "9999-12-31") >= generated}
exported_social = {e["n"] for e in data.get("social", [])}
for name in sorted(expected_social - exported_social):
    problems.append(f"social series missing from venues.json: {name}")

if problems:
    print("app/data/venues.json is stale (generated " + generated + "):\n  " + "\n  ".join(problems))
    sys.exit(1)
print(f"venues.json is consistent with the seeds ({len(exported)} events).")
