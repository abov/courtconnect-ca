"""Fail when the newest quality scorecard line is worse than the one before it (ADR 0019 gate 4, no-regression).

`make quality` appends a line to docs/data_quality_trend.csv. This compares the newest line with the previous line, or
with the last line of the same file on another git ref (`--base-ref origin/main`, what a merge gate on a PR would use).
Regression = any of:
  - venues fell by more than --max-venue-drop-pct (default 1.0, the ADR 0019 value)
  - "seen in 35 days" fell
  - more SLAs fail than before (sla_total - sla_met rose)
  - any dbt test fails (tests_fail > 0)
Exit 1 on regression. Blank values (older lines) are skipped, not failed.
"""
import argparse, csv, io, subprocess, sys
from pathlib import Path

TREND = Path(__file__).resolve().parents[1] / "docs" / "data_quality_trend.csv"


def num(row, col):
    try:
        return float(row.get(col, ""))
    except ValueError:
        return None


def rows_of(text):
    return list(csv.DictReader(io.StringIO(text)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--max-venue-drop-pct", type=float, default=1.0)
    ap.add_argument("--base-ref", help="git ref whose copy of the trend file supplies the previous line (default: the previous line in this file)")
    args = ap.parse_args()

    rows = rows_of(TREND.read_text(encoding="utf-8"))
    if not rows:
        sys.exit("trend file has no rows")
    new = rows[-1]
    if args.base_ref:
        rel = TREND.relative_to(TREND.parents[1]).as_posix()
        out = subprocess.run(["git", "show", f"{args.base_ref}:{rel}"], capture_output=True, text=True, cwd=TREND.parents[1])
        if out.returncode:
            sys.exit(f"git show {args.base_ref}:{rel} failed: {out.stderr.strip()}")
        base_rows = rows_of(out.stdout)
        if not base_rows:
            sys.exit("base trend file has no rows")
        old = base_rows[-1]
        if new["date"] == old["date"] and new == old:
            print(f"No new scorecard line vs {args.base_ref} ({new['date']}): nothing to compare.")
            return
    elif len(rows) < 2:
        print("Only one scorecard line: nothing to compare.")
        return
    else:
        old = rows[-2]

    problems = []
    v_old, v_new = num(old, "venues"), num(new, "venues")
    if v_old and v_new is not None:
        drop = (v_old - v_new) / v_old * 100
        if drop > args.max_venue_drop_pct:
            problems.append(f"venues fell {drop:.1f}% ({int(v_old)} -> {int(v_new)}), limit {args.max_venue_drop_pct}%")
    s_old, s_new = num(old, "seen_35d_pct"), num(new, "seen_35d_pct")
    if s_old is not None and s_new is not None and s_new < s_old:
        problems.append(f"seen in 35 days fell ({s_old} -> {s_new})")
    met_old, tot_old, met_new, tot_new = (num(old, "sla_met"), num(old, "sla_total"), num(new, "sla_met"), num(new, "sla_total"))
    if None not in (met_old, tot_old, met_new, tot_new) and (tot_new - met_new) > (tot_old - met_old):
        problems.append(f"SLAs failing rose ({int(tot_old - met_old)} -> {int(tot_new - met_new)})")
    fails = num(new, "tests_fail")
    if fails:
        problems.append(f"{int(fails)} dbt test(s) failing")

    print(f"Scorecard {old['date']} -> {new['date']}")
    if problems:
        print("Scorecard REGRESSION:")
        print("\n".join(f"- {p}" for p in problems))
        sys.exit(1)
    print("Scorecard OK: no regression.")


if __name__ == "__main__":
    main()
