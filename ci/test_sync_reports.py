"""Offline test for ingestion/sync_reports.py (no network): runs the fixture CSV through the real import code against a throwaway
copy of the seed headers and checks what lands where. Run: python ci/test_sync_reports.py"""
import csv, shutil, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ingestion"))
import sync_reports as sr  # noqa: E402
itp = sr.itp

tmp = Path(tempfile.mkdtemp())
try:
    for name in sr.SEED_FILES:   # headers only: the test owns the rows
        header = (itp.SEEDS / name).read_text(encoding="utf-8").splitlines()[0]
        (tmp / name).write_text(header + "\n", encoding="utf-8")
    (tmp / "all_racquet.csv").write_text("sport\nPickleball\nTennis\n", encoding="utf-8")
    (tmp / "sport_aliases.csv").write_text("alias,sport\n", encoding="utf-8")
    itp.SEEDS, itp.VENUES_JSON = tmp, ROOT / "ci" / "fixtures" / "reports_venues.json"

    rows = list(csv.DictReader((ROOT / "ci" / "fixtures" / "reports_approved.csv").open(newline="", encoding="utf-8")))
    res = sr.import_rows(rows)
    status = [s for _, s, _ in res]
    assert status == ["added", "added", "added", "error", "error"], res
    assert "email" in res[3][2] and "https" in res[4][2], res

    def seed(name):
        return list(csv.DictReader((tmp / name).open(newline="", encoding="utf-8")))

    mv = seed("manual_venues.csv")
    assert len(mv) == 1 and mv[0]["venue_key"] == "report-aaaaaaaaaa" and mv[0]["sport"] == "Pickleball", mv
    assert mv[0]["confirmation"] == "reported" and mv[0]["confirmed_on"] == "2025-10-01" and mv[0]["access"] == "public"
    assert "form:10022025140311" in mv[0]["evidence"] and "credit: courtfan" in mv[0]["evidence"], mv[0]["evidence"]
    assert "https://example.org/parks/test-park" in mv[0]["evidence"]
    vc = seed("venue_confirmations.csv")
    assert len(vc) == 1 and vc[0]["confirmed_by"] == "form:10022025140311" and vc[0]["method"] == "reported", vc
    leads = seed("venue_leads.csv")
    assert [l["lead_id"] for l in leads] == ["form-10032025091500", "form-10042025100000"], leads
    assert all(l["source_type"] == "word_of_mouth" and l["status"] == "new" for l in leads), leads

    again = [s for _, s, _ in sr.import_rows(rows[:3])]   # second run: nothing is added twice
    assert again == ["skipped"] * 3, again
    assert len(seed("manual_venues.csv")) == 1 and len(seed("venue_leads.csv")) == 2
    print("sync_reports: ok")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
