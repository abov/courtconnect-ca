"""Offline test for ci/sync_reports.py (no network): runs the fixture CSV through the real import code against a throwaway copy of
the seed headers and checks what lands where. Run: python ci/test_sync_reports.py"""
import csv, shutil, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ci"))
import sync_reports as sr  # noqa: E402
ip = sr.ip

tmp = Path(tempfile.mkdtemp())
try:
    for name in sr.SEED_FILES:   # headers only: the test owns the rows
        header = (ip.SEEDS / name).read_text(encoding="utf-8").splitlines()[0]
        (tmp / name).write_text(header + "\n", encoding="utf-8")
    (tmp / "all_racquet.csv").write_text("sport\nPickleball\nTennis\n", encoding="utf-8")
    (tmp / "sport_aliases.csv").write_text("alias,sport\n", encoding="utf-8")
    ip.SEEDS, ip.VENUES_JSON = tmp, ROOT / "ci" / "fixtures" / "reports_venues.json"

    rows = list(csv.DictReader((ROOT / "ci" / "fixtures" / "reports_approved.csv").open(newline="", encoding="utf-8")))
    assert sr.import_rows(rows) == (3, 0, 2)          # 1 report on a pin + 2 leads; the email/phone row and the http link are rejected
    assert sr.import_rows(rows) == (0, 3, 2)          # second run: nothing is added twice

    def seed(name):
        return list(csv.DictReader((tmp / name).open(newline="", encoding="utf-8")))

    mv = seed("manual_venues.csv")
    assert len(mv) == 1 and mv[0]["sport"] == "Pickleball" and mv[0]["confirmation"] == "reported", mv
    assert mv[0]["confirmed_on"] == "2025-10-01" and "courtfan" in mv[0]["evidence"], mv[0]
    assert "https://example.org/parks/test-park" in mv[0]["evidence"]
    vc = seed("venue_confirmations.csv")
    assert len(vc) == 1 and vc[0]["confirmed_by"].startswith("form:") and vc[0]["method"] == "reported", vc
    assert len(seed("venue_leads.csv")) == 2
    assert "@" not in "".join(r["evidence"] for r in mv) and "555" not in (tmp / "manual_venues.csv").read_text(encoding="utf-8")
    print("sync_reports: ok")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
