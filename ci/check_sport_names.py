"""Fail when a sport name used in a seed or the sport counts disagree with the sports sheet.

The Google Sheet (synced to transform/seeds/all_racquet.csv) is the source of the sports list (CLAUDE.md rule).
A renamed or removed sport must be carried through the seeds and the two count settings at the same sync
(docs/monthly_refresh.md step 2). Checks:
  1. rows in all_racquet.csv == EXPECTED_SPORTS (ingestion/sync_sports_sheet.py) == expected_racket_sports (transform/dbt_project.yml)
  2. every sport named in the seeds below exists in all_racquet.csv (multi-sport cells split on ';')
Run in CI or by an agent after `make sync-sports`. Exit 1 on any mismatch.
"""
import csv, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "transform" / "seeds"
# file: (columns holding sport names, split multi-value cells on ';')
SPORT_COLUMNS = {
    "manual_venues.csv": ["sport"],
    "manual_walls.csv": ["sports_suited"],
    "sport_also_played.csv": ["sport", "also_sport"],
    "sport_aliases.csv": ["sport"],          # the alias column is free text on purpose
    "place_sport_overrides.csv": ["sport"],
    "watch_events.csv": ["sport"],
    "social_events.csv": ["sport"],
    "player_platforms.csv": ["sports"],
}


def read(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    errors = []
    sheet = [r["sport"].strip() for r in read(SEEDS / "all_racquet.csv")]
    known = set(sheet)
    if len(known) != len(sheet):
        errors.append("all_racquet.csv: duplicate sport names")

    script = (ROOT / "ingestion" / "sync_sports_sheet.py").read_text(encoding="utf-8")
    m_script = re.search(r"^EXPECTED_SPORTS\s*=\s*(\d+)", script, re.M)
    project = (ROOT / "transform" / "dbt_project.yml").read_text(encoding="utf-8")
    m_dbt = re.search(r"^\s*expected_racket_sports:\s*(\d+)", project, re.M)
    if not m_script or not m_dbt:
        errors.append("could not find EXPECTED_SPORTS in sync_sports_sheet.py or expected_racket_sports in dbt_project.yml")
    else:
        counts = {"sheet rows": len(sheet), "EXPECTED_SPORTS": int(m_script.group(1)), "expected_racket_sports": int(m_dbt.group(1))}
        if len(set(counts.values())) != 1:
            errors.append(f"sport counts disagree: {counts}")

    for name, cols in SPORT_COLUMNS.items():
        for i, row in enumerate(read(SEEDS / name), start=2):
            for col in cols:
                for sport in (s.strip() for s in (row.get(col) or "").split(";")):
                    if sport and sport not in known:
                        errors.append(f"{name}:{i}: {col} '{sport}' is not in all_racquet.csv")

    if errors:
        print("Sport name check FAILED:")
        print("\n".join(f"- {e}" for e in errors))
        sys.exit(1)
    print(f"Sport name check OK: {len(sheet)} sports, seeds use only known names.")


if __name__ == "__main__":
    main()
