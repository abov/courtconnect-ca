"""Offline check of ingestion/osm_snapshot_diff.py on a tiny fixture (ci/fixtures/osm_diff): kinds, seed, manifest rotation, guards. No network."""
from __future__ import annotations

import csv
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ingestion"))
import osm_snapshot_diff as d  # noqa: E402

FIX = ROOT / "ci" / "fixtures" / "osm_diff"


def run(tmp: Path, *extra: str) -> str:
    r = subprocess.run([sys.executable, str(ROOT / "ingestion" / "osm_snapshot_diff.py"), "--new-dir", str(tmp), "--seed", str(tmp / "seed.csv"),
                        "--no-verify", *extra], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return r.stdout


def rows(path: Path) -> list[dict]:
    return list(csv.DictReader(path.open(encoding="utf-8")))


def main() -> None:
    # classification of a gone id from its tags in OSM today
    assert d.classify_gone(None) == "deleted"
    assert d.classify_gone({"sport": "tennis", "leisure": "pitch"}) == "still_listed"      # the extract missed it
    assert d.classify_gone({"sport": "tennis;pickleball", "club": "sport"}) == "still_listed"
    assert d.classify_gone({"leisure": "pitch"}) == "retagged"                             # sport tag deleted
    assert d.classify_gone({"sport": "tennis"}) == "retagged"                              # leisure tag deleted
    assert d.classify_gone({"sport": "basketball", "leisure": "pitch"}) == "retagged"

    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        (tmp / "osm_snapshot").mkdir()
        shutil.copy(FIX / "old_osm_courts.csv", tmp / "osm_snapshot" / "osm_courts.csv")
        shutil.copy(FIX / "new_osm_courts.csv", tmp / "osm_courts.csv")
        shutil.copy(FIX / "new_osm_courts_nv.csv", tmp / "osm_courts_nv.csv")

        # 2 of 7 elements gone is over the 10% guard: refused, nothing written, snapshot kept
        out = run(tmp)
        assert "no earlier snapshot" in out                                             # Nevada had no manifest: baseline saved
        assert "partial extract" in out and not (tmp / "osm_snapshot_diff.csv").exists(), out
        assert len(rows(tmp / "osm_snapshot" / "osm_courts.csv")) == 7
        assert not (tmp / "seed.csv").exists()

        out = run(tmp, "--force")
        got = {(r["kind"], r["osm_type"] + "/" + r["osm_id"]) for r in rows(tmp / "osm_snapshot_diff.csv")}
        assert got == {("gone", "way/2"), ("gone", "way/3"), ("moved", "node/4"), ("renamed", "node/5"), ("sport_changed", "node/6"), ("new", "node/7")}, got
        seed = {r["element_id"]: r for r in rows(tmp / "seed.csv")}
        assert set(seed) == {"way/2", "way/3"}, seed
        assert seed["way/2"]["last_seen_extract"] == "2026-10-23" and seed["way/2"]["gone_in_extract"] == "2026-11-06" and seed["way/2"]["sport"] == "tennis"
        assert len(rows(tmp / "osm_snapshot" / "osm_courts_nv.csv")) == 1
        assert {r["osm_id"] for r in rows(tmp / "osm_snapshot" / "osm_courts.csv")} == {"1", "4", "5", "6", "7", "8"}   # rotated to the new extract

        # same extract again: nothing to diff, seed unchanged
        assert "nothing to diff" in run(tmp)
        assert len(rows(tmp / "seed.csv")) == 2

        # an element that came back and vanished again takes the newer dates; a first sighting is otherwise kept
        again = [{"kind": "deleted", "osm_type": "way", "osm_id": "2", "name": "Beta Courts", "sport": "tennis", "leisure": "pitch", "region": "CA",
                  "lat": "34.2", "lon": "-118.2", "old_extract": "2026-11-06T09:00:00+00:00", "new_extract": "2026-12-04T09:00:00+00:00", "detail": ""}]
        assert d.update_gone_seed(again, tmp / "seed.csv") == 1
        assert d.update_gone_seed(again, tmp / "seed.csv") == 0
        seed = {r["element_id"]: r for r in rows(tmp / "seed.csv")}
        assert seed["way/2"]["gone_in_extract"] == "2026-12-04" and seed["way/2"]["kind"] == "deleted" and seed["way/3"]["kind"] == "gone"
    print("OSM snapshot diff OK.")


if __name__ == "__main__":
    main()
