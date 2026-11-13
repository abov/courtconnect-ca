"""Write the aggregate CSVs the Evidence.dev dashboard reads (dashboard/sources/courtconnect/*.csv).

    python ingestion/export_dashboard_data.py        (or: make dashboard-data)

Only counts and dates that are already public leave the warehouse: the scorecard history, the numbers on the How it's built page
(app/data/build_stats.json), the feedback issue counts (docs/feedback_log.csv), daily site views (docs/usage_daily.csv), event counts by name (docs/usage_events.csv),
the ML scores (docs/ml_metrics.csv, docs/review_priority.csv, docs/reader_pilot_results.csv), Google Trends search interest per metro and sport next to venue counts (docs/search_interest_vs_coverage.csv) and, from the map export, per-sport and per-city venue counts with how complete they are.
No venue rows, names, addresses or contacts. The CSVs are
generated and git-ignored; run `make quality`, `make stats` and `make app-data` first so they are current.
"""
from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dashboard" / "sources" / "courtconnect"


def write(name: str, header: list[str], rows: list[list]) -> None:
    with (OUT / name).open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote dashboard/sources/courtconnect/{name}: {len(rows)} rows")


def slug(text: str) -> str:
    return "".join(c if c.isalnum() else " " for c in text.lower()).strip()


def completeness(vs: list[dict]) -> list[float | None]:
    """Shares of venues with: a real name (court, operator or places-directory name, same as the scorecard), a street address, a website,
    and a hand check (visited, or stated by the operator). Completeness is the mean of the first three.
    Likely private-residence pins (`h`, ADR 0016) are left out: they never get a street and have no website, so they could never score.
    A place that is all such pins has no score (None)."""
    vs = [v for v in vs if not v.get("h")]
    n = len(vs)
    if not n:
        return [None] * 5
    real = sum(v["q"] in ("c", "p") for v in vs) / n
    addr = sum(bool(v["a"]) for v in vs) / n
    web = sum(bool(v["w"]) for v in vs) / n
    checked = sum(v.get("cf") in ("v", "o") for v in vs) / n
    return [round(x, 4) for x in (real, addr, web, checked, (real + addr + web) / 3)]


def live_issues() -> list[tuple[str, str]] | None:
    """(opened, closed) dates for every GitHub issue, straight from GitHub, so the scheduled Pages build is current.
    Only runs in CI (GITHUB_ACTIONS); locally, and on any failure, the dashboard falls back to docs/feedback_log.csv."""
    if not os.environ.get("GITHUB_ACTIONS"):
        return None
    try:
        out = subprocess.run(["gh", "issue", "list", "--state", "all", "--limit", "2000", "--json", "createdAt,closedAt"],
                             capture_output=True, text=True, check=True, timeout=60).stdout
        return [(i["createdAt"][:10], (i["closedAt"] or "")[:10]) for i in json.loads(out)]
    except (subprocess.SubprocessError, OSError, ValueError, KeyError):
        print("live issue fetch failed; using docs/feedback_log.csv")
        return None


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "docs" / "data_quality_trend.csv", OUT / "trend.csv")
    print("wrote dashboard/sources/courtconnect/trend.csv: copy of docs/data_quality_trend.csv")

    s = json.loads((ROOT / "app" / "data" / "build_stats.json").read_text(encoding="utf-8"))
    # Venue and sport counts come from the map file itself so they always match the map; quality numbers keep the scorecard's own date.
    mj = json.loads((ROOT / "app" / "data" / "venues.json").read_text(encoding="utf-8"))
    m = mj["meta"]
    # sports with no venue split in two: ones that need no official court (play anywhere, `w` on the sport) and ones with none mapped yet
    anywhere = sum(1 for x in mj["sports"] if x["v"] == 0 and x.get("w"))
    none_yet = sum(1 for x in mj["sports"] if x["v"] == 0 and not x.get("w"))
    write("stats.csv",
          ["as_of", "scorecard_as_of", "venues", "sports_with_venues", "sports_total", "named_pct", "sla_met", "sla_total", "tests_pass", "models", "seeds", "adrs",
           "gold_pairs", "gold_wrong_merges", "gold_missed", "map_as_of", "map_venues", "map_sports_with_venues", "map_sports_total", "map_sports_anywhere", "map_sports_none"],
          [[s["as_of"], s["scorecard_as_of"], s["venues"], s["sports_with_venues"], s["sports_total"], s["named_pct"], s["sla_met"], s["sla_total"], s["tests_pass"],
            s["models"], s["seeds"], s["adrs"], s["gold"]["pairs"], s["gold"]["wrong_merges"], s["gold"]["missed"],
            m["generated"], m["venues"], m["sports_with_venues"], m["sports_total"], anywhere, none_yet]])

    # Feedback issues: one row per day from the first report to today, so the chart shows open vs handled over time.
    log = live_issues()
    if log is None:
        with (ROOT / "docs" / "feedback_log.csv").open(encoding="utf-8") as f:
            log = [(r["received_on"], r["resolved_on"]) for r in csv.DictReader(f) if r["channel"] == "github-issue"]
    if log:
        opened, closed = Counter(o for o, _ in log), Counter(c for _, c in log if c)
        # GitHub dates are UTC, so a close can be dated after the local "today"; never cut it off.
        day, end, rows, n_open = date.fromisoformat(min(opened)), max(date.today(), date.fromisoformat(max([*opened, *closed]))), [], 0
        while day <= end:
            k = day.isoformat()
            n_open += opened[k] - closed[k]
            rows.append([k, opened[k], closed[k], n_open])
            day += timedelta(days=1)
        write("issues.csv", ["date", "opened", "closed", "open_now"], rows)

    # GoatCounter omits days with no hits; fill them with 0 so the chart has no gaps and "days" is the real span.
    with (ROOT / "docs" / "usage_daily.csv").open(encoding="utf-8") as f:
        seen = {r["day"]: [int(r["page_views"]), int(r["events"])] for r in csv.DictReader(f)}
    day, last, rows = date.fromisoformat(min(seen)), date.fromisoformat(max(seen)), []
    while day <= last:
        rows.append([day.isoformat(), *seen.get(day.isoformat(), [0, 0])])
        day += timedelta(days=1)
    write("views.csv", ["day", "page_views", "events"], rows)

    venues = json.loads((ROOT / "app" / "data" / "venues.json").read_text(encoding="utf-8"))
    write("sport_coverage.csv", ["sport", "venues", "status"], [[x["n"], x["v"], x["s"]] for x in venues["sports"]])

    # Event counts by day, name and detail (the vocabulary in docs/goat_analysis.md): the ask box, sport picks, link-outs, demand by city.
    with (ROOT / "docs" / "usage_events.csv").open(encoding="utf-8") as f:
        ev = list(csv.DictReader(f))
    write("events.csv", ["day", "event", "detail", "count"], [[r["day"], r["event"], r["detail"], int(r["count"])] for r in ev])
    demand = defaultdict(lambda: defaultdict(int))   # event name -> slug(detail) -> count
    for r in ev:
        demand[r["event"]][slug(r["detail"])] += int(r["count"])

    # How complete the data is per sport and per city, next to how much each is looked at. Demand is small while traffic is small: directional only.
    by_sport = defaultdict(list)
    by_city = defaultdict(list)
    for v in venues["venues"]:
        for p in v["p"]:
            by_sport[p[0]].append(v)
        if v["c"]:
            by_city[(v["c"], v["r"])].append(v)
    rows = []
    for i, sp in enumerate(venues["sports"]):
        vs = by_sport.get(i)
        k = slug(sp["n"])
        picks, links, asks = demand["sport-pick"][k], demand["linkout-sport"][k], demand["ask-sport"][k]
        if vs and not sp.get("b"):   # sports assumed playable on another sport's courts just mirror that sport's venues; the map marks them inferred
            rows.append([sp["n"], len(vs), *completeness(vs), picks, links, asks, picks + links + asks, sp["s"]])
    write("sport_scorecard.csv", ["sport", "venues", "real_name_share", "address_share", "website_share", "hand_checked_share", "completeness",
                                   "picks", "linkouts", "asks", "demand", "status"], rows)
    rows = []
    for (city, region), vs in by_city.items():
        opens = demand["demand-where"][slug(f"{city} {region}")]
        if len(vs) >= 15 or opens:   # small towns only appear once someone has looked at them
            rows.append([city, region, len(vs), sum(bool(v.get("h")) for v in vs), *completeness(vs), opens])
    rows.sort(key=lambda r: (-r[-1], -r[2]))
    write("city_scorecard.csv", ["city", "region", "venues", "private_pins", "real_name_share", "address_share", "website_share", "hand_checked_share",
                                  "completeness", "opens"], rows)

    # Google Trends interest per metro and sport next to venues and completeness (written from the warehouse by `make interest`; relative, sampled).
    shutil.copyfile(ROOT / "docs" / "search_interest_vs_coverage.csv", OUT / "search_interest.csv")
    print("wrote dashboard/sources/courtconnect/search_interest.csv: copy of docs/search_interest_vs_coverage.csv")

    # ML: the review-queue ranker's score history and queue, and what the page reader found, all from committed files.
    shutil.copyfile(ROOT / "docs" / "ml_metrics.csv", OUT / "ml_metrics.csv")
    print("wrote dashboard/sources/courtconnect/ml_metrics.csv: copy of docs/ml_metrics.csv")
    with (ROOT / "docs" / "review_priority.csv").open(encoding="utf-8") as f:
        queue = Counter((r["model_guess"], r["sport_name"]) for r in csv.DictReader(f))
    write("review_queue.csv", ["model_guess", "sport", "rows"], [[g, sp, n] for (g, sp), n in sorted(queue.items())])
    with (ROOT / "docs" / "reader_pilot_results.csv").open(encoding="utf-8") as f:
        reader = Counter((r["field"], r["outcome"]) for r in csv.DictReader(f))
    write("reader_outcomes.csv", ["field", "outcome", "facts"], [[fl, o, n] for (fl, o), n in sorted(reader.items())])


if __name__ == "__main__":
    main()
