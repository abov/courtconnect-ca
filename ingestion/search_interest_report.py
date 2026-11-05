"""Print Google Trends search interest versus venues per metro and write the dashboard's aggregate CSV (docs/search_interest_plan.md).

    python ingestion/search_interest_report.py        (or: make interest)

Reads marts.mart_search_vs_coverage in courtconnect.duckdb (run `dbt build` first; the warehouse is not changed). Writes docs/search_interest_vs_coverage.csv,
one row per metro and sport with data: no venue rows, commit it after a refresh (the Pages build has no warehouse and the dashboard reads this file).
Interest is relative and sampled, not volumes; 'thin' sports are noisy. A gap candidate is a place to look for missing venues, not proof of one.
"""
from __future__ import annotations

import csv
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "courtconnect.duckdb"
CSV = ROOT / "docs" / "search_interest_vs_coverage.csv"


def table(con, sql: str) -> str:
    cur = con.execute(sql)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    if not rows:
        return "_none_\n"
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join("" if v is None else str(v) for v in r) + " |" for r in rows]
    return "\n".join(out) + "\n"


def write_csv(con) -> None:
    cur = con.execute("""select metro_name as metro, sport_name as sport, interest_index, interest_rank, venues_found as venues,
                                completeness_share, confidence, gap_candidate, exported_on
                         from marts.mart_search_vs_coverage where interest_index is not null order by sport_name, interest_index desc, metro_name""")
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    with CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(["" if v is None else str(v).lower() if isinstance(v, bool) else v for v in r] for r in rows)
    print(f"wrote {CSV.relative_to(ROOT).as_posix()}: {len(rows)} rows\n")


def main() -> None:
    if not DB.exists():
        raise SystemExit("courtconnect.duckdb not found: run `python ingestion/fresh_db.py`")
    con = duckdb.connect(str(DB), read_only=True)
    write_csv(con)
    exported, = con.execute("select max(exported_on) from marts.mart_search_vs_coverage").fetchone()
    print(f"# Search interest vs venues (Google Trends export {exported}; relative, sampled; re-export about quarterly)\n")
    print("## Gap candidates (interest index >= 50, 3 or fewer venues, busiest sports only)\n")
    print(table(con, """select metro_name as metro, sport_name as sport, interest_index as interest, venues_found as venues, interest_rank as rank
                        from marts.mart_search_vs_coverage where gap_candidate order by interest_index desc"""))
    print("## Venues near each metro anchor, by sport (busiest sports)\n")
    print(table(con, """select metro_name as metro,
                               max(case when sport_name = 'Tennis' then venues_found end) as tennis,
                               max(case when sport_name = 'Pickleball' then venues_found end) as pickleball,
                               max(case when sport_name = 'Padel' then venues_found end) as padel,
                               max(case when sport_name = 'Badminton' then venues_found end) as badminton,
                               max(case when sport_name = 'Table Tennis' then venues_found end) as table_tennis
                        from marts.mart_search_vs_coverage group by 1 order by 1"""))


if __name__ == "__main__":
    main()
