"""Offline test: make report keeps the snapshot file when only the dated title line would change (no churn diff).
No DuckDB, no network: duckdb and overpass are stubbed before the module is imported. Run: python ci/test_export_coverage_report.py"""
import pathlib
import sys
import tempfile
import types

sys.modules.setdefault("duckdb", types.ModuleType("duckdb"))
sys.modules.setdefault("overpass", types.ModuleType("overpass"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "ingestion"))
import export_coverage_report as e  # noqa: E402

with tempfile.TemporaryDirectory() as d:
    p = pathlib.Path(d) / "snap.md"
    a = "# Coverage snapshot (2026-11-24)\n\nbody 1\n"
    assert e.write_if_changed(p, a) is True                      # new file: written
    b = "# Coverage snapshot (2026-11-25)\n\nbody 1\n"
    assert e.write_if_changed(p, b) is False                     # same numbers, new date: kept
    assert p.read_text(encoding="utf-8") == a
    c = "# Coverage snapshot (2026-11-25)\n\nbody 2\n"
    assert e.write_if_changed(p, c) is True                      # real change: written
    assert p.read_text(encoding="utf-8") == c

print("export_coverage_report: write_if_changed ok")
