"""Print the ADR 0013 usage metrics, plus demand versus coverage, from the GoatCounter export.

    python ingestion/extract_goatcounter.py     # refresh data first (needs GOATCOUNTER_API_TOKEN)
    python ingestion/goat_report.py             # last 28 days, markdown on stdout
    python ingestion/goat_report.py --days 7 --csv some.csv

Read-only. Demand versus coverage joins the sport picks to `marts.mart_sport_gaps` in courtconnect.duckdb when that file exists.
Counts are approximate (ad blockers and Do Not Track hide some visits) and directional only: docs/goat_analysis.md.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rawdir import raw_path  # noqa: E402

DB = Path(__file__).resolve().parent.parent / "courtconnect.duckdb"
SLUG = "regexp_replace(regexp_replace(lower({c}), '[^a-z0-9.]+', '-', 'g'), '^-+|-+$', '', 'g')"


def table(con, sql: str, params=None) -> str:
    cur = con.execute(sql, params or [])
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    if not rows:
        return "_none yet_\n"
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join("" if v is None else str(v) for v in r) + " |" for r in rows]
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--days", type=int, default=28)
    ap.add_argument("--csv", default=raw_path("goatcounter_daily.csv"))
    args = ap.parse_args()
    if not Path(args.csv).exists():
        sys.exit(f"{args.csv} not found: run ingestion/extract_goatcounter.py first.")

    con = duckdb.connect()
    # one clean view: leading slash removed, only the window asked for
    con.execute(f"""create view h as
        select cast(day as date) as day, regexp_replace(path, '^/', '') as path, title, is_event, count
        from read_csv_auto('{Path(args.csv).as_posix()}')
        where cast(day as date) >= current_date - {int(args.days)}""")
    def n(cond: str) -> int:
        return con.execute(f"select coalesce(sum(count), 0) from h where {cond}").fetchone()[0]

    views = n("not is_event")
    opens, links = n("path = 'event/venue-open'"), n("path = 'event/linkout'")
    contrib = n("path in ('event/suggest-change', 'event/osm-edit', 'event/report-form')")
    pct = lambda a, b: f"{100 * a / b:.0f}%" if b else "n/a"   # noqa: E731
    print(f"# GoatCounter, last {args.days} days (directional only)\n")
    print(f"- Page views: **{views}**; venue opens: **{opens}** ({opens / views:.1f} per view)" if views else "- No page views in this window.")
    print(f"- North star, link-outs: **{links}** (link-out rate {pct(links, opens)} of venue opens)")
    print(f"- Contributions (suggest / OSM / report form): **{contrib}**\n")

    print("## Link-outs per week\n")
    print(table(con, "select date_trunc('week', day) as week, sum(count) as linkouts from h where path = 'event/linkout' group by 1 order by 1"))
    for title, prefix in [("Link-outs by domain (which providers matter)", "linkout-domain"), ("Link-outs by kind", "linkout-kind"),
                          ("Link-outs by sport filter active", "linkout-sport"), ("Mode switches", "mode"), ("Filters turned on", "filter"),
                          ("Searches that found nothing", "search-miss")]:
        print(f"## {title}\n")
        print(table(con, f"select max(title) as value, sum(count) as n from h where path like 'event/{prefix}/%' group by path order by n desc limit 15"))
    print("## Where people came from (?ref= tags)\n")
    print(table(con, "select replace(path, 'event/ref/', '') as ref, sum(count) as visits from h where path like 'event/ref/%' group by 1 order by 2 desc"))
    print("## Habits\n")
    print(table(con, """select replace(path, 'event/', '') as event, sum(count) as n from h
        where path in ('event/share', 'event/shortlist-add', 'event/shortlist-open', 'event/shortlist-copy', 'event/focus-on',
                       'event/welcome-back', 'event/this-week-open', 'event/map-key') group by 1 order by 2 desc"""))

    if DB.exists():
        db = duckdb.connect(str(DB), read_only=True)
        gaps = db.execute("select sport_name, venues_found, coverage_status from marts.mart_sport_gaps").fetchall()
        con.execute("create table gaps(sport_name varchar, venues_found bigint, coverage_status varchar)")
        con.executemany("insert into gaps values (?, ?, ?)", gaps)
        print("## Demand versus coverage (sport picks vs venues on the map)\n")
        print("`empty picks` = a sport pick that left nothing on the map: the clearest gap signal.\n")
        print(table(con, f"""
            with picks as (select path, max(title) as t, sum(count) as picks from h where path like 'event/sport-pick/%' group by path),
                 empties as (select path, sum(count) as e from h where path like 'event/empty-play/%' group by path)
            select p.t as sport, p.picks, coalesce(e.e, 0) as empty_picks, g.venues_found, g.coverage_status
            from picks p
            left join gaps g on {SLUG.format(c='g.sport_name')} = replace(p.path, 'event/sport-pick/', '')
            left join empties e on replace(e.path, 'event/empty-play/', '') = replace(p.path, 'event/sport-pick/', '')
            order by p.picks desc limit 20"""))
    else:
        print("(courtconnect.duckdb not found: run `python ingestion/fresh_db.py` to add the coverage comparison.)")


if __name__ == "__main__":
    main()
