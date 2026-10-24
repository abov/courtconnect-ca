"""Keep new tournament sources from slipping in unnoticed (docs/tournament_refresh.md, "Finding new event sites").

docs/event_sources.csv lists every site the tournament runs read. This check fails when:
  - a watch_events row links to a site that has no row in event_sources.csv (add the site, status active or candidate),
  - a linked site is marked rejected,
  - a row has a bad status or a duplicate domain.
Rows with status `candidate` are sites found but not yet read: the next run reads them or marks them rejected.
"""
import csv, sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {"active", "blocked", "candidate", "rejected"}


def main(root=ROOT):
    errors, sources = [], {}
    with (root / "docs" / "event_sources.csv").open(newline="", encoding="utf-8") as f:
        for i, r in enumerate(csv.DictReader(f), start=2):
            d = (r["domain"] or "").strip().lower()
            if not d or "/" in d:
                errors.append(f"event_sources.csv:{i}: domain must be a bare host like example.com")
            if r["status"] not in STATUSES:
                errors.append(f"event_sources.csv:{i}: status must be one of {', '.join(sorted(STATUSES))}")
            if d in sources:
                errors.append(f"event_sources.csv:{i}: {d} is listed twice")
            sources[d] = r

    def lookup(host):
        return next((s for d, s in sources.items() if host == d or host.endswith("." + d)), None)

    with (root / "transform" / "seeds" / "watch_events.csv").open(newline="", encoding="utf-8") as f:
        for i, r in enumerate(csv.DictReader(f), start=2):
            for col in ("info_url", "tickets_url"):
                host = (urlparse(r[col]).hostname or "").removeprefix("www.")
                if not host:
                    continue
                s = lookup(host)
                if not s:
                    errors.append(f"watch_events.csv:{i}: {host} (from {r['event_key']}) is not in docs/event_sources.csv: add a row")
                elif s["status"] == "rejected":
                    errors.append(f"watch_events.csv:{i}: {host} is marked rejected in docs/event_sources.csv")
    for d, s in sources.items():
        if s["status"] == "candidate":
            print(f"reminder: candidate source {d} is not read yet: read it or mark it rejected")
    if errors:
        print("\n".join(errors))
        return 1
    print("event sources check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
