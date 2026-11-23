"""Offline test for ci/weekly_audit.py: synthetic PR lists, no gh, no network. Run: python ci/test_weekly_audit.py"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ci"))
import weekly_audit as w  # noqa: E402

NOW = datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)


def iso(days_ago):
    return (NOW - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


def pr(n, files=("transform/seeds/manual_venues.csv",), ok=True, days_ago=1, branch="claude/x"):
    return {"number": n, "title": f"PR {n}", "mergedAt": iso(days_ago), "createdAt": iso(days_ago), "headRefName": branch,
            "files": [{"path": f} for f in files],
            "statusCheckRollup": [{"name": "dbt-build", "conclusion": "SUCCESS" if ok else "FAILURE"}]}


def main():
    # guarded paths
    for f in (".github/workflows/ci.yml", "docs/decisions/0019-x.md", "CLAUDE.md", "SECURITY.md", "ingestion/load_raw.py",
              "transform/models/a.sql", "app/index.html", ".env.example"):
        assert w.GUARDED.match(f), f
    for f in ("transform/seeds/manual_venues.csv", "app/data/venues.json", "docs/status.md", "docs/README.md"):
        assert not w.GUARDED.match(f), f

    merged = [pr(i) for i in range(1, 31)]
    merged.append(pr(31, files=(".github/workflows/ci.yml",)))
    merged.append(pr(32, ok=False))
    merged.append(pr(33, days_ago=10))  # outside the window
    chain = [{"createdAt": iso(3), "headRefName": "claude/tournaments-2026-11-20"}]
    text, alert = w.build_digest(merged, chain, NOW)
    assert alert is None
    assert "32 PR(s) merged" in text, text.splitlines()[0]
    assert "#31" in text and "#32" in text and "#33" not in text
    assert "Spot-check sample: 5 of 30" in text  # 10% of 30 = 3, minimum 5
    again, _ = w.build_digest(merged, chain, NOW)
    assert text == again  # reproducible

    # the sample grows with volume
    big = [pr(i) for i in range(1, 101)]
    assert "10 of 100" in w.build_digest(big, chain, NOW)[0]

    # chain alert: stale, missing, and non-chain branches do not count
    assert w.build_digest(merged, [{"createdAt": iso(25), "headRefName": "claude/refresh-x"}], NOW)[1]
    assert w.build_digest(merged, [], NOW)[1]
    assert w.build_digest(merged, [{"createdAt": iso(1), "headRefName": "claude/mx-walls"}], NOW)[1]
    assert w.build_digest(merged, [{"createdAt": iso(19), "headRefName": "claude/refresh-x"}], NOW)[1] is None

    # a merged PR with no dbt-build entry counts as not green
    nocheck = pr(40)
    nocheck["statusCheckRollup"] = []
    assert "#40" in w.build_digest([nocheck], chain, NOW)[0].split("## Touched")[0]
    print("weekly audit tests passed")


main()
