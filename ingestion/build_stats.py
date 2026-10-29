"""Write app/data/build_stats.json: the measured numbers shown on app/how-its-built.html.

    python ingestion/build_stats.py            (or: make stats)   run after `make quality`, in the refresh PR
    python ingestion/build_stats.py --check    CI: the file is well formed and dated like the newest scorecard row

Nothing is typed in by hand. Every number comes from a file or check that already exists:
  scorecard   last row of docs/data_quality_trend.csv (venues, sports, service levels, dbt tests)
  sports      app/data/venues.json meta.sports_total
  structure   file counts in transform/, ci/ and docs/decisions/
  gold set    ingestion/eval_match_gold.py against the local DuckDB; when the database is missing or locked the
              previous values in this file are kept (CI never builds the full warehouse)
  Overture    docs/planet_scale_benchmark.json (bytes the real extracts fetched vs the size of the themes)
The page shows `as_of` beside the numbers, and --check fails when the file is older than the newest scorecard row,
so a refresh that runs `make quality` but forgets `make stats` is caught, not shipped.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ingestion"))
OUT = ROOT / "app" / "data" / "build_stats.json"
TREND = ROOT / "docs" / "data_quality_trend.csv"
VENUES = ROOT / "app" / "data" / "venues.json"
BENCH = ROOT / "docs" / "planet_scale_benchmark.json"
KEYS = ["as_of", "venues", "sports_with_venues", "sports_total", "named_pct", "sla_met", "sla_total", "tests_pass", "tests_fail",
        "models", "seeds", "custom_tests", "adrs", "ci_checks", "gold", "overture"]


def last_trend_row() -> dict:
    rows = list(csv.DictReader(TREND.open(encoding="utf-8")))
    return rows[-1]


def gold_numbers(previous: dict | None) -> dict:
    """Pairs, wrong merges and missed merges from the gold set; the old values when the warehouse cannot be read."""
    import eval_match_gold as gold

    rows = gold.load_gold()
    try:
        tally, _wrong, stale = gold.evaluate(rows)
        t = tally["all"]
        return {"pairs": len(rows), "wrong_merges": t["fp"], "missed": t["fn"], "stale": len(stale)}
    except Exception as e:  # no database in this checkout, or the DuckDB UI holds it open
        if previous and previous.get("gold"):
            print(f"gold set not re-scored ({type(e).__name__}); keeping the previous values", file=sys.stderr)
            return {**previous["gold"], "pairs": len(rows)}
        sys.exit(f"gold set cannot be scored and there are no previous values: {e}")


def overture_numbers() -> dict:
    b = json.loads(BENCH.read_text(encoding="utf-8"))
    fetched = sum(b["themes"][t]["extract_step"]["bytes"] for t in ("places", "addresses"))
    size = sum(b["themes"][t]["release_bytes"] for t in ("places", "addresses"))
    return {"release": b["release"], "run_on": b["run_on"], "fetched_mb": round(fetched / 1e6), "themes_gb": round(size / 1e9, 1)}


def build() -> dict:
    t = last_trend_row()
    meta = json.loads(VENUES.read_text(encoding="utf-8"))["meta"]
    previous = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else None
    return {
        "as_of": t["date"],
        "venues": int(t["venues"]),
        "sports_with_venues": int(t["sports_with_venues"]),
        "sports_total": int(meta["sports_total"]),
        "named_pct": float(t["named_pct"]),
        "sla_met": int(t["sla_met"]),
        "sla_total": int(t["sla_total"]),
        "tests_pass": int(t["tests_pass"]),
        "tests_fail": int(t["tests_fail"]),
        "models": len(list((ROOT / "transform" / "models").rglob("*.sql"))),
        "seeds": len(list((ROOT / "transform" / "seeds").glob("*.csv"))),
        "custom_tests": len(list((ROOT / "transform" / "tests").glob("*.sql"))),
        "adrs": len(list((ROOT / "docs" / "decisions").glob("[0-9][0-9][0-9][0-9]-*.md"))),
        "ci_checks": len(list((ROOT / "ci").glob("check_*.py"))),
        "gold": gold_numbers(previous),
        "overture": overture_numbers(),
    }


def check() -> None:
    problems = []
    if not OUT.exists():
        sys.exit(f"{OUT.relative_to(ROOT)} is missing: run `make stats` and commit it")
    d = json.loads(OUT.read_text(encoding="utf-8"))
    for k in KEYS:
        if k not in d:
            problems.append(f"missing key: {k}")
    if not problems:
        if d["as_of"] != last_trend_row()["date"]:
            problems.append(f"as_of {d['as_of']} is not the newest scorecard row {last_trend_row()['date']}: run `make stats` after `make quality`")
        for k in ("venues", "sports_total", "models", "seeds", "adrs"):
            if not isinstance(d[k], int) or d[k] <= 0:
                problems.append(f"{k} must be a positive integer")
        if d["gold"].get("wrong_merges") is None or d["gold"].get("missed") is None:
            problems.append("gold needs wrong_merges and missed")
    if problems:
        sys.exit("build_stats.json check failed:\n  " + "\n  ".join(problems))
    print(f"build_stats.json ok: as of {d['as_of']}, {d['venues']} venues, gold set {d['gold']['pairs']} pairs")


def main() -> None:
    if "--check" in sys.argv:
        return check()
    d = build()
    OUT.write_text(json.dumps(d, indent=1) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}: as of {d['as_of']}, {d['venues']} venues, {d['models']} models, {d['tests_pass']} dbt tests passing, "
          f"gold set {d['gold']['pairs']} pairs ({d['gold']['wrong_merges']} wrong, {d['gold']['missed']} missed)")


if __name__ == "__main__":
    main()
