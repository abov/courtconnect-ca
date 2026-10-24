"""Keep R2 Sports events from falling through the cracks (docs/tournament_refresh.md, R2 row).

Every R2 event the refresh reads gets one row in docs/r2_seen.csv (tid, decision), so the next run only has to look at
TIDs it has not decided on. This check fails when:
  - a watch_events row sourced from R2 does not link to its own r2-push.asp?TID= page (the generic search page is not a source),
  - a TID in watch_events is missing from r2_seen.csv, or is not marked `added` with that event_key,
  - an r2_seen row marked `added` has no matching watch_events row,
  - a decision is not one of the allowed values.
Rows left `pending` only print a reminder: they never fail CI, but the refresh must clear them.
"""
import csv, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECISIONS = {"added", "out_of_region", "past", "duplicate", "not_racket", "pending"}
TID = re.compile(r"r2sports\.com/r2-push\.asp\?TID=(\d+)", re.I)
# Rows that predate this check and link to the R2 search page. Put the event's TID in info_url (and a row in r2_seen.csv) and delete the entry.
GRANDFATHERED = {"nightmare-before-christmas-racquetball-2026", "racquetball-players-championship-2027"}


def rows(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main(root=ROOT):
    errors, seen = [], {}
    for i, r in enumerate(rows(root / "docs" / "r2_seen.csv"), start=2):
        where = f"r2_seen.csv:{i}"
        tid = (r["tid"] or "").strip()
        if not tid.isdigit():
            errors.append(f"{where}: tid must be a number")
        if r["decision"] not in DECISIONS:
            errors.append(f"{where}: decision must be one of {', '.join(sorted(DECISIONS))}")
        if r["decision"] == "added" and not (r["event_key"] or "").strip():
            errors.append(f"{where}: an added event needs its event_key")
        if tid in seen:
            errors.append(f"{where}: TID {tid} is listed twice")
        seen[tid] = r

    keys = set()
    for i, r in enumerate(rows(root / "transform" / "seeds" / "watch_events.csv"), start=2):
        keys.add(r["event_key"])
        links = f"{r['info_url']} {r['tickets_url']}"
        if "r2sports.com" not in links:
            continue
        m = TID.search(links)
        if not m:
            if r["event_key"] not in GRANDFATHERED:
                errors.append(f"watch_events.csv:{i}: {r['event_key']} cites R2 Sports without its r2-push.asp?TID= link")
            continue
        s = seen.get(m.group(1))
        if not s or s["decision"] != "added" or s["event_key"] != r["event_key"]:
            errors.append(f"watch_events.csv:{i}: TID {m.group(1)} needs a docs/r2_seen.csv row marked added with event_key {r['event_key']}")

    errors += [f"r2_seen.csv: TID {t} is marked added but event_key {s['event_key']} is not in watch_events.csv"
               for t, s in seen.items() if s["decision"] == "added" and s["event_key"] not in keys]
    for t, s in seen.items():
        if s["decision"] == "pending":
            print(f"reminder: R2 TID {t} (seen {s['seen_on']}) is still pending: read it and decide")
    if errors:
        print("\n".join(errors))
        return 1
    print("R2 event check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
