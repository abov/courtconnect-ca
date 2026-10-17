"""Guard for docs/review_priority.csv (written by ingestion/rank_review_queue.py). Run in CI before dbt; needs no database.

Fails when a row whose site is flagged dead (website_status = dead) is followed by a live-site row: dead-domain rows must sort
last, because a parked or expired site cannot settle the sport. Warns (does not fail) when a domain flagged dead in
transform/seeds/website_overrides.csv still sits in the queue unmarked: re-run `make rank-review` to refresh the file.
"""
import csv, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rows = list(csv.DictReader((ROOT / "docs" / "review_priority.csv").open(newline="", encoding="utf-8")))
errors = []
seen_dead = None
for r in rows:
    if r.get("website_status") == "dead":
        seen_dead = seen_dead or r["review_priority"]
    elif seen_dead:
        errors.append(f"review_priority {r['review_priority']} has a live site but follows dead-site row {seen_dead}: re-run make rank-review")
        break
flagged = {(r["domain"] or "").strip().lower() for r in csv.DictReader((ROOT / "transform" / "seeds" / "website_overrides.csv").open(newline="", encoding="utf-8")) if (r["status"] or "").strip().lower() == "dead"}
stale = sorted({r["website_domain"] for r in rows if r.get("website_status") != "dead" and (r.get("website_domain") or "").lower() in flagged})
if stale:
    print("warning: dead in website_overrides but not marked dead in review_priority.csv (re-run make rank-review): " + ", ".join(stale))
if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"review priority check passed ({sum(r.get('website_status') == 'dead' for r in rows)} dead-site rows sorted last of {len(rows)})")
