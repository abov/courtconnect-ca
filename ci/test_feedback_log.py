"""Offline test for ci/feedback_log.py (no network). Run: python ci/test_feedback_log.py"""
import sys, tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import feedback_log as fl  # noqa: E402

today = date(2026, 11, 4)
issues = [
    {"number": 533, "title": "Chat not working", "author": {"login": "abov"}, "labels": [], "state": "OPEN",
     "createdAt": "2026-11-03T05:50:24Z", "closedAt": None, "comments": [], "url": "u533", "closedByPullRequestsReferences": []},
    {"number": 112, "title": "Change: Marine Avenue Park", "author": {"login": "abov"}, "labels": [{"name": "venue-change"}],
     "state": "CLOSED", "createdAt": "2026-10-15T10:04:01Z", "closedAt": "2026-10-15T19:43:51Z",
     "comments": [{"createdAt": "2026-10-20T00:00:00Z"}], "url": "u112", "closedByPullRequestsReferences": [{"number": 132}]},
]
rows = []
added, closed_now, reopened, late = fl.sync(rows, issues, today)
assert added == ["gh-533", "gh-112"] and not closed_now and not reopened and late == ["gh-112"]
by = {r["id"]: r for r in rows}
assert by["gh-112"]["status"] == "done" and by["gh-112"]["resolution"] == "PR #132" and by["gh-112"]["kind"] == "wrong-data"
assert by["gh-533"]["status"] == "open" and by["gh-533"]["kind"] == "other"

by["gh-533"]["kind"] = "bug"                       # a person's edit survives the next sync
issues[0].update(state="CLOSED", closedAt="2026-11-04T01:00:00Z")
added, closed_now, reopened, late = fl.sync(rows, issues, today)
assert not added and closed_now == ["gh-533"] and by["gh-533"]["kind"] == "bug" and by["gh-533"]["status"] == "closed"

mid = fl.add_row(rows, "message", "friend-padel", "bug", "Map is slow on my phone", "", today)
assert mid == "message-20261104-1" and by.get("gh-533")
tmp = Path(tempfile.mkdtemp()) / "log.csv"
fl.write_log(rows, tmp)
assert len(fl.read_log(tmp)) == 3
print("ok")
