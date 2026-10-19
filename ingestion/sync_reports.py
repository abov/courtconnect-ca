"""Import approved community reports (Google Form -> response sheet -> reviewed by the owner) into the seeds.

    python ingestion/sync_reports.py --dry-run     # print what would be added, change nothing
    python ingestion/sync_reports.py               # write the seed rows (then: dbt build, make app-data, open a PR)
    python ingestion/sync_reports.py --file rows.csv   # read a local CSV instead of the web (tests, offline)

The response sheet is private. Only its `approved` tab (rows the owner marked `approved`) is "published to the web" as CSV, and that
URL is kept in .env as REPORTS_CSV_URL (never committed). This script only reads that CSV (public, no login, no personal contact).

Each row goes through ci/issue_to_pr.py's apply_report(), the same code as GitHub issue reports: a report on a map pin becomes a
manual_venues row at the pin's coordinates with confirmation 'reported' (not confirmed) plus a venue_confirmations row; a correction or
closure, or a venue the seeds cannot place, becomes a lead for a reviewer. Evidence names the row (form:<id>) and the date seen.
Rows already imported are skipped (the form:<id> token is already in a seed). Rows with an email address or phone number, or a link
that is not https, are skipped and listed so the owner can edit the sheet.
"""
from __future__ import annotations

import argparse
import csv
import io
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ci"))
import issue_to_pr as itp  # noqa: E402  (shared row-writing logic)

USER_AGENT = "courtconnect-ca/0.1 (+https://github.com/abov/courtconnect-ca)"
SEED_FILES = ["all_racquet.csv", "sport_aliases.csv", "manual_venues.csv", "venue_confirmations.csv", "venue_actions.csv", "venue_leads.csv"]
CHANGE = {  # "What are you reporting?" choice (prefix) -> the wording apply_report() understands
    "a racket sport": "Report a racket sport played here (community form)",
    "i visited": "Confirm (community form)",
    "something is wrong": "Correction or closure (community form)",
}
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(?<!\d)(?:\+?\d[\s().-]?){9,}\d(?!\d)")


def col(row, prefix):
    """Value of the column whose header starts with prefix (the form's question titles; tolerant of the '(optional...)' suffixes)."""
    for k, v in row.items():
        if k and k.strip().lower().startswith(prefix.lower()):
            return (v or "").strip()
    return ""


def iso_date(text):
    """Sheets shows the form's date answer as M/D/YYYY or YYYY-MM-DD depending on locale."""
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(text.strip(), fmt).date().isoformat()
        except ValueError:
            pass
    return text.strip()


def row_token(row):
    """Stable id of a response: its timestamp's digits (the sheet row number moves when rows are filtered or deleted)."""
    digits = re.sub(r"\D", "", col(row, "Timestamp"))
    return f"form:{digits}" if len(digits) >= 8 else ""


def already_imported(token):
    return any(token in (itp.SEEDS / name).read_text(encoding="utf-8") for name in SEED_FILES[2:])


def import_row(row):
    """Write one approved row into the seeds; returns the summary line. Raises itp.ReportError when the row cannot be used."""
    token = row_token(row)
    if not token:
        raise itp.ReportError("no timestamp, so the row has no stable id")
    free = " ".join(col(row, c) for c in ("Venue name", "City", "Sport", "What did you see", "Name or handle"))   # not date/map id/link
    if EMAIL.search(free + " " + col(row, "Link to a public page")) or PHONE.search(free):
        raise itp.ReportError("contains an email address or phone number; edit the sheet to remove it, then it imports next time")
    choice = col(row, "What are you reporting").lower()
    change = next((v for k, v in CHANGE.items() if choice.startswith(k)), None)
    if not change:
        raise itp.ReportError(f"unknown 'What are you reporting?' answer: {choice[:60]!r}")
    credit = itp.clean(col(row, "Name or handle"), 60)
    origin = f"community form report {token}" + (f" (credit: {credit})" if credit else "")
    return itp.apply_report(
        ref=token.replace(":", "-"), lead_id=token.replace(":", "-"), origin=origin, user=token, by=token,
        venue=col(row, "Venue name"), city=col(row, "City"), change=change, ltype="",
        source=col(row, "Link to a public page"), price="", seen=iso_date(col(row, "Date you saw")),
        details=col(row, "What did you see"), sport_text=col(row, "Sport"), map_id_raw=col(row, "Map ID"),
        lead_source="word_of_mouth")


def import_rows(rows):
    """Returns (token, status, text) per row; status is 'added', 'skipped' (already imported) or 'error'."""
    out = []
    for row in rows:
        token = row_token(row) or "form:?"
        if token != "form:?" and already_imported(token):
            out.append((token, "skipped", "already imported"))
            continue
        try:
            out.append((token, "added", import_row(row)))
        except itp.ReportError as e:
            out.append((token, "error", str(e)))
    return out


def fetch_csv(url):
    from urllib.request import Request, urlopen
    if urlparse(url).scheme != "https" or urlparse(url).hostname != "docs.google.com":
        sys.exit("REPORTS_CSV_URL must be the https docs.google.com 'publish to web' CSV link of the approved tab.")
    with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=30) as r:
        return r.read().decode("utf-8-sig")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true", help="print what would be added; change no file")
    ap.add_argument("--file", help="read this CSV instead of the published sheet")
    args = ap.parse_args()

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8-sig")
    else:
        from dotenv import load_dotenv
        load_dotenv()
        url = os.environ.get("REPORTS_CSV_URL", "").strip()
        if not url:
            sys.exit("Set REPORTS_CSV_URL in .env (the approved tab's published CSV link; see .env.example).")
        text = fetch_csv(url)
    rows = list(csv.DictReader(io.StringIO(text)))
    # With no approved rows the published tab is empty; anything else without the form's columns is a sign-in page or the wrong tab.
    if text.strip() and "venue name" not in text.splitlines()[0].lower():
        sys.exit("That is not the approved-tab CSV (no 'Venue name' column); is the tab still published to the web?")

    tmp = None
    if args.dry_run:   # apply against a throwaway copy of the seeds
        tmp = Path(tempfile.mkdtemp())
        for name in SEED_FILES:
            shutil.copy(itp.SEEDS / name, tmp / name)
        itp.SEEDS = tmp
    try:
        results = import_rows(rows)
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)

    verb = "would add" if args.dry_run else "added"
    for token, status, text in results:
        print(f"{token}: {verb if status == 'added' else status}: {text}")
    n = sum(s == "added" for _, s, _ in results)
    print(f"{len(rows)} approved rows: {n} {verb}, {sum(s == 'skipped' for _, s, _ in results)} already imported, "
          f"{sum(s == 'error' for _, s, _ in results)} need attention.")
    if n and not args.dry_run:
        print("Next: dbt build, make app-data, commit the seeds + app/data/venues.json, open a PR (runbook step 2b).")


if __name__ == "__main__":
    main()
