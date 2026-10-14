"""Write docs/data_quality.md (a data-quality scorecard) and append a row to docs/data_quality_trend.csv.

    python ingestion/export_quality_scorecard.py            (or: make quality)
    python ingestion/export_quality_scorecard.py --strict   exit 1 if an SLA is breached

Reads the DuckDB build. Every SLA below is a stated, adjustable target; a breach is reported, and only fails with --strict.
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import date, datetime
from pathlib import Path

import duckdb

TREND = Path("docs/data_quality_trend.csv")
OUT = Path("docs/data_quality.md")
RUN_RESULTS = Path("transform/target/run_results.json")

# SLAs (days). Change here and the scorecard follows.
SLA_EXTRACT_DAYS = 90        # OpenStreetMap extract age
SLA_ACTIONS_DAYS = 60        # oldest current link-out verification (matches assert_venue_actions_fresh)
SLA_EVENTS_DAYS = 14         # oldest upcoming event verification (bi-weekly refresh runbook; the dbt test warns at 120)
SLA_LINKCHECK_DAYS = 60      # website liveness checks
SLA_DEAD_SITE_PCT = 10.0     # share of checked venue websites that are dead
SLA_SEEN_DAYS = 35          # monthly freshness: a venue counts as fresh when some source saw it within this many days (mart_venue_confidence.last_seen_on)
SLA_SEEN_PCT = 99.0          # share of venues that must be fresh; undated rows count as stale and are listed so they get a date
SLA_NAMED_PCT = 25.0         # goal: share of venues with a real (non-guessed, non-empty) name; baseline 11.6% on 2026-10-13


def days_since(ts) -> int | None:
    if not ts:
        return None
    s = str(ts)[:10]
    try:
        return (date.today() - date.fromisoformat(s)).days
    except ValueError:
        return None


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    strict = "--strict" in sys.argv
    con = duckdb.connect("courtconnect.duckdb", read_only=True)
    q = lambda sql: con.execute(sql).fetchall()
    today = date.today().isoformat()

    venues, named, sited, in_osm, in_places, in_manual = q("""
        select count(*), count(*) filter (where name_source in ('court_name','operator','manual','places_directory')),
               count(*) filter (where website_usable is not null and website_usable <> ''),
               count(*) filter (where in_osm), count(*) filter (where in_places), count(*) filter (where in_manual)
        from (select venue_id, any_value(name_source) name_source, any_value(website_usable) website_usable,
                     bool_or(in_osm) in_osm, bool_or(in_places) in_places, bool_or(in_manual) in_manual
              from marts.mart_venue_finder where lat is not null and lon is not null group by venue_id)""")[0]
    sports_total, sports_covered, sports_empty = q("""
        select count(*), count(*) filter (where venues_found > 0), count(*) filter (where venues_found = 0) from marts.mart_sport_gaps""")[0]
    conf = dict(q("select confirmation_level, count(*) from staging.stg_manual_venues group by 1"))
    leads = dict(q("select status, count(*) from staging.stg_venue_leads group by 1"))
    actions_cur, actions_old, actions_age = q("""
        select count(*), count(*) filter (where verified_on < current_date - 60), max(current_date - verified_on)
        from staging.stg_venue_actions where end_date is null or end_date >= current_date""")[0]
    events_up, events_old, events_age = q("""
        select count(*), count(*) filter (where verified_on < current_date - 14), max(current_date - verified_on)
        from staging.stg_watch_events where end_date is null or end_date >= current_date""")[0]
    seen_total, seen_fresh, seen_undated, seen_oldest = q(f"""
        select count(*), count(*) filter (where last_seen_on >= current_date - {SLA_SEEN_DAYS}),
               count(*) filter (where last_seen_on is null), min(last_seen_on)
        from marts.mart_venue_confidence""")[0]
    seen_pct = round(100.0 * seen_fresh / seen_total, 1) if seen_total else 0.0
    stale_rows = q(f"""
        select coalesce(venue_name, '(no name)'), venue_source, coalesce(cast(last_seen_on as varchar), 'undated')
        from marts.mart_venue_confidence where last_seen_on is null or last_seen_on < current_date - {SLA_SEEN_DAYS}
        order by last_seen_on nulls first, venue_name limit 25""")
    band_rows = q("""
        select coalesce(v.region, '?'), c.confidence_band, count(*)
        from marts.mart_venue_confidence c left join core.dim_venue v on v.venue_id = c.venue_id
        group by 1, 2""")
    extract_age = days_since(q("select max(extracted_at) from raw.osm_courts")[0][0])
    link_age = days_since(q("select max(checked_at) from raw.website_checks")[0][0])
    checked, dead = q("select coalesce(sum(checked),0), coalesce(sum(dead),0) from marts.mart_website_quality where source in ('osm','manual')")[0]
    dead_pct = round(100.0 * dead / checked, 1) if checked else 0.0
    named_pct = round(100.0 * named / venues, 1) if venues else 0.0

    tests = {"pass": 0, "warn": 0, "fail": 0, "error": 0}
    if RUN_RESULTS.exists():
        for r in json.loads(RUN_RESULTS.read_text(encoding="utf-8")).get("results", []):
            if str(r.get("unique_id", "")).startswith("test."):
                tests[r["status"]] = tests.get(r["status"], 0) + 1

    # (name, measured, target, unit, ok)
    slas = [
        ("OSM extract age", extract_age, SLA_EXTRACT_DAYS, "days", extract_age is not None and extract_age <= SLA_EXTRACT_DAYS),
        ("Oldest current link-out check", actions_age, SLA_ACTIONS_DAYS, "days", actions_age is None or actions_age <= SLA_ACTIONS_DAYS),
        ("Oldest upcoming-event check", events_age, SLA_EVENTS_DAYS, "days", events_age is None or events_age <= SLA_EVENTS_DAYS),
        ("Website link-check age", link_age, SLA_LINKCHECK_DAYS, "days", link_age is not None and link_age <= SLA_LINKCHECK_DAYS),
        ("Dead venue websites (of checked)", dead_pct, SLA_DEAD_SITE_PCT, "%", dead_pct <= SLA_DEAD_SITE_PCT),
        (f"Venues seen in the last {SLA_SEEN_DAYS} days", seen_pct, SLA_SEEN_PCT, "% (minimum)", seen_pct >= SLA_SEEN_PCT),
        ("Venues with a real name", named_pct, SLA_NAMED_PCT, "% (minimum)", named_pct >= SLA_NAMED_PCT),
    ]
    breaches = [s for s in slas if not s[4]]

    L = [f"# Data quality scorecard", "",
         f"Generated {today} by `make quality` (`ingestion/export_quality_scorecard.py`) from the current DuckDB build. "
         "Targets are stated service levels, not guarantees: they are set in the script and a breach is reported, not hidden.", "",
         "## Service levels", "", "| Measure | Now | Target | Status |", "|---|---|---|---|"]
    for name, val, tgt, unit, ok in slas:
        shown = "no data" if val is None else f"{val} {unit.split(' ')[0]}"
        cmp = ">=" if "minimum" in unit else "<="
        L.append(f"| {name} | {shown} | {cmp} {tgt} {unit.split(' ')[0]} | {'OK' if ok else '**BREACH**'} |")
    L += ["", f"**{len(slas) - len(breaches)} of {len(slas)} service levels met.**", "",
          "## Coverage", "",
          f"- Venues on the map: **{venues:,}** ({in_osm:,} in OpenStreetMap, {in_places:,} in Overture places, {in_manual:,} hand-curated; sources overlap).",
          f"- Venues with a real name: **{named:,}** ({named_pct}%). The rest carry a name guessed from the park or school, or none.",
          f"- Venues with a usable website: **{sited:,}** ({round(100.0 * sited / venues, 1) if venues else 0}%).",
          f"- Sports on the sheet: **{sports_total}**; with at least one venue: **{sports_covered}**; empty: **{sports_empty}**.", "",
          "## Trust labels (hand-curated venues)", "",
          "| Confirmation | Venues |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in sorted(conf.items(), key=lambda kv: -kv[1])]
    L += ["", "Visited = seen in person; official = stated on the operator's own page; reported = told to us, not verified. "
          "Inferred data is labeled inferred on the map and never counted as confirmed.", ""]
    regions = sorted({r for r, _, _ in band_rows})
    band_n = {(r, b): n for r, b, n in band_rows}
    L += ["## Confidence bands (all venues, inferred)", "",
          "Rule-based score from `mart_venue_confidence` (rules_v2): high >= 60, medium 30-59, low < 30. "
          "It is an inferred heuristic for prioritizing review, not a probability; it is not shown on the map.", "",
          "| Band | All | " + " | ".join(regions) + " |", "|---" * (len(regions) + 2) + "|"]
    for b in ("high", "medium", "low"):
        tot = sum(band_n.get((r, b), 0) for r in regions)
        L.append(f"| {b} | {tot:,} | " + " | ".join(f"{band_n.get((r, b), 0):,}" for r in regions) + " |")
    L.append("| total | " + f"{sum(band_n.values()):,} | " + " | ".join(f"{sum(band_n.get((r, b), 0) for b in ('high', 'medium', 'low')):,}" for r in regions) + " |")
    L += ["",
          "## Freshness", "",
          f"- OSM extract: {extract_age if extract_age is not None else 'unknown'} days old.",
          f"- Current link-outs: {actions_cur}; {actions_old} older than {SLA_ACTIONS_DAYS} days.",
          f"- Upcoming events: {events_up}; {events_old} not re-checked in {SLA_EVENTS_DAYS}+ days.",
          f"- Website liveness check: {link_age if link_age is not None else 'unknown'} days old; {dead} of {checked} checked venue sites dead ({dead_pct}%).",
          f"- Venues seen by any source in the last {SLA_SEEN_DAYS} days: {seen_fresh:,} of {seen_total:,} ({seen_pct}%); oldest date {seen_oldest or 'none'}; "
          f"{seen_undated} undated. Sources: OSM extract date, Overture release date, hand-added confirmation, link-out check "
          "(monthly runbook: docs/monthly_refresh.md).", ""]
    if stale_rows:
        L += [f"Stale or undated venues (first {len(stale_rows)}):", "", "| Venue | Source | Last seen |", "|---|---|---|"]
        L += [f"| {n} | {src} | {d} |" for n, src, d in stale_rows]
        L += [""]
    L += [
          "## Open leads", "", "| Status | Leads |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in sorted(leads.items(), key=lambda kv: -kv[1])]
    L += ["", "## Tests", "",
          (f"Last dbt run: {tests['pass']} tests passed, {tests['warn']} warned, {tests['fail'] + tests['error']} failed." if RUN_RESULTS.exists()
           else "No dbt run results found (run `dbt build` first)."),
          "", "History: [data_quality_trend.csv](data_quality_trend.csv) (one row per run)."]
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")

    row = {"date": today, "venues": venues, "named_pct": named_pct, "sites_dead_pct": dead_pct, "sports_with_venues": sports_covered,
           "events_upcoming": events_up, "actions_current": actions_cur, "extract_age_days": extract_age if extract_age is not None else "",
           "events_oldest_check_days": events_age if events_age is not None else "", "seen_35d_pct": seen_pct, "sla_met": len(slas) - len(breaches), "sla_total": len(slas),
           "tests_pass": tests["pass"], "tests_warn": tests["warn"], "tests_fail": tests["fail"] + tests["error"]}
    old = [r for r in csv.DictReader(TREND.open(encoding="utf-8")) if r["date"] != today] if TREND.exists() else []
    with TREND.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row), lineterminator="\n")
        w.writeheader()
        w.writerows(old + [row])
    print(f"Wrote {OUT}: {len(slas) - len(breaches)}/{len(slas)} service levels met" + (f"; breaches: {', '.join(s[0] for s in breaches)}" if breaches else ""))
    if strict and breaches:
        sys.exit(1)


if __name__ == "__main__":
    main()
