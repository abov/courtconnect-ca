"""Turn approved community-form reports (Google Form -> Google Sheet) into seed edits: `make sync-reports`.

The owner reviews responses in the sheet (a plausibility and spam check) and types `approved` in the `review` column. The sheet's
`approved` tab is published to the web as CSV (File -> Share -> Publish to web) and that URL lives in .env (gitignored):

    REPORTS_CSV_URL=https://docs.google.com/spreadsheets/d/e/2PACX-.../pub?gid=<approved gid>&single=true&output=csv

Each row runs through the same code as a GitHub "Suggest a change" issue (ci/issue_to_pr.py process()), so the rules are the same:
reports on existing pins become `reported` manual_venues rows + a venue_confirmations row, corrections and closures become leads.
The CSV is read-only, so rows are not marked imported in the sheet; instead a row is skipped when its timestamp already appears in
the seeds ("community form response <timestamp>"). Run it, review `git diff`, then `make build` and open a normal PR.

    python ci/sync_reports.py            # fetch REPORTS_CSV_URL
    python ci/sync_reports.py --file x.csv   # read a local export instead (testing)
    python ci/sync_reports.py --dry-run      # print what would be added; change no file (add --file x.csv to preview a local export)

Anonymous rows: confirmed_by = form:<timestamp>. The reporter's optional credit name goes into the evidence text only.
The text is untrusted: it is only written through the csv module, URLs must be https, nothing is executed.
"""
import csv, io, os, re, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import issue_to_pr as ip  # noqa: E402

CHOICES = {   # the form's "What are you reporting?" options -> the issue form's "What are you suggesting" wording
    "a racket sport is played here": "Report a racket sport played here",
    "i visited, or the operator's page says so": "Confirm a venue's details",
    "something is wrong or it closed": "Correction or closure",
}
SEED_FILES = ["all_racquet.csv", "sport_aliases.csv", "manual_venues.csv", "venue_confirmations.csv", "venue_actions.csv", "venue_leads.csv"]
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(?<!\d)(?:\+?\d[\s().-]?){9,}\d(?!\d)")
REQUIRED = ["Timestamp", "Venue name", "City", "What are you reporting?", "Date you saw it", "What did you see?"]


def load_dotenv_if_any():
    try:
        from dotenv import load_dotenv
        load_dotenv(ip.ROOT / ".env")
    except ImportError:
        pass


def fetch(url):
    u = urlparse(url)
    if u.scheme != "https" or u.hostname != "docs.google.com":
        sys.exit("REPORTS_CSV_URL must be an https://docs.google.com/ published-CSV link.")
    import requests
    r = requests.get(url, timeout=30, headers={"User-Agent": "courtconnect-ca/0.1 (+https://github.com/abov/courtconnect-ca)"})
    r.raise_for_status()
    if "csv" not in r.headers.get("content-type", "") and not r.text.startswith("Timestamp"):
        sys.exit("That URL did not return CSV (is the tab published to the web as CSV?).")
    return r.text


def parse_when(text, fmts):
    for f in fmts:
        try:
            return datetime.strptime(text.strip(), f)
        except ValueError:
            pass
    return None


def seed_text():
    return "\n".join((ip.SEEDS / n).read_text(encoding="utf-8")
                     for n in ("manual_venues.csv", "venue_confirmations.csv", "venue_actions.csv", "venue_leads.csv")).lower()


def row_to_form(r):
    stamp = parse_when(r["Timestamp"], ("%m/%d/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"))
    seen = parse_when(r["Date you saw it"], ("%m/%d/%Y", "%Y-%m-%d"))
    if not stamp:
        raise ip.Rejected(f"unreadable timestamp {r['Timestamp']!r}")
    if not seen:
        raise ip.Rejected(f"unreadable date {r['Date you saw it']!r}")
    change = CHOICES.get(r["What are you reporting?"].strip().lower())
    if not change:
        raise ip.Rejected(f"unknown report type {r['What are you reporting?']!r}")
    details = r["What did you see?"]
    free = " ".join([r["Venue name"], r["City"], details, r.get("Sport", ""), r.get("Name or handle to credit you (optional, shown publicly)", "")])
    if EMAIL.search(free + " " + r.get("Link to a public page (optional, https)", "")) or PHONE.search(free):
        raise ip.Rejected("contains an email address or phone number; remove it in the sheet, then it imports next time")
    if change.startswith("Confirm") and "visited" not in details.lower():
        details = f"Reporter chose 'I visited, or the operator's page says so'. {details}"   # lets a confirmation without a link pass as a visit
    form = {"Venue name": r["Venue name"], "City": r["City"], "Map ID": r.get("Map ID", ""),
            "What are you suggesting": change, "Sport played here": r.get("Sport", ""),
            "Date you saw": seen.date().isoformat(), "What did you see": details,
            "Link to a public page": r.get("Link to a public page (optional, https)", "")}
    return stamp.strftime("%Y-%m-%dT%H:%M:%S"), form


def import_rows(rows):
    """Run each approved row through ip.process(); returns (imported, already_in_seeds, rejected) and prints one line per row."""
    done = skipped = bad = 0
    for r in rows:
        if not (r.get("Timestamp") or "").strip():
            continue
        try:
            stamp, form = row_to_form(r)
            if f"community form response {stamp}".lower() in seed_text():
                skipped += 1
                continue
            credit = ip.clean(r.get("Name or handle to credit you (optional, shown publicly)", ""), 60)
            origin = f"community form response {stamp}" + (f" (credited as {credit})" if credit else "")
            num = stamp.replace("-", "").replace(":", "")
            print(f"{stamp}: " + ip.process(form, num, f"form:{stamp}", origin, f"form:{stamp}", "form", "community_form"))
            done += 1
        except ip.Rejected as e:
            bad += 1
            print(f"{r.get('Timestamp')}: NOT imported: {e}")
    return done, skipped, bad


def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args
    if "--file" in args:
        text = Path(args[args.index("--file") + 1]).read_text(encoding="utf-8")
    else:
        load_dotenv_if_any()
        url = os.environ.get("REPORTS_CSV_URL", "").strip()
        if not url:
            sys.exit("Set REPORTS_CSV_URL in .env (the approved tab's published-CSV link; see docs/community_reports_plan.md).")
        text = fetch(url)
    rows = list(csv.DictReader(io.StringIO(text)))
    missing = [c for c in REQUIRED if rows and c not in rows[0]]
    if missing:
        sys.exit(f"The CSV is missing columns {missing}: the form's question titles must match the plan exactly.")
    tmp = None
    if dry:   # write into a throwaway copy of the seeds, so nothing in the repo changes
        tmp = Path(tempfile.mkdtemp())
        for n in SEED_FILES:
            shutil.copy(ip.SEEDS / n, tmp / n)
        ip.SEEDS = tmp
    try:
        done, skipped, bad = import_rows(rows)
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
    print(f"{done} {'would be imported (dry run, nothing written)' if dry else 'imported'}, {skipped} already in the seeds, {bad} rejected."
          + ("" if dry else " Review `git diff`, then `make build`."))


if __name__ == "__main__":
    main()
