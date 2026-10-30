"""Offline test for ingestion/init_fork.py: a throwaway repo layout, no git, no network.
Checks the region config it writes, that owner seeds lose their rows but keep the header, that mapping seeds are untouched, and that bad input is refused.
Run: python ci/test_init_fork.py"""
import json, shutil, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ingestion"))
import init_fork as f  # noqa: E402

tmp = Path(tempfile.mkdtemp())
try:
    (tmp / "ingestion").mkdir()
    (tmp / "ingestion" / "regions.json").write_text(
        json.dumps({"note": "keep me", "regions": {"CA": {"name": "california"}}, "metros": {"la": {}}}), encoding="utf-8")
    seeds = tmp / "transform" / "seeds"
    seeds.mkdir(parents=True)
    for name in ["manual_venues", "venue_name_official", "venue_city_official", "osm_sport_map", "all_racquet", "sport_aliases"]:
        (seeds / f"{name}.csv").write_text("a,b\n1,2\n3,4\n", encoding="utf-8")

    regions = f.parse_regions([["TX", "texas", "25.8", "-106.7", "36.6", "-93.5", "114690"]])
    metros = f.parse_metros([["austin", "30.1", "-97.95", "30.5", "-97.55", "TX"]], regions)

    plan = f.apply(tmp, regions, metros, write=False)                      # dry run changes nothing
    assert (seeds / "manual_venues.csv").read_text(encoding="utf-8").count("\n") == 3 and any("venue_name_official" in p for p in plan), plan
    assert json.loads((tmp / "ingestion" / "regions.json").read_text(encoding="utf-8"))["metros"] == {"la": {}}

    f.apply(tmp, regions, metros, write=True)
    cfg = json.loads((tmp / "ingestion" / "regions.json").read_text(encoding="utf-8"))
    assert cfg["note"] == "keep me" and list(cfg["regions"]) == ["TX"] and cfg["regions"]["TX"]["cache"] == "tx_border.wkt", cfg
    assert cfg["regions"]["TX"]["relation"] == 114690 and cfg["metros"]["austin"]["states"] == ["TX"], cfg
    for name in ["manual_venues", "venue_name_official", "venue_city_official"]:   # glob venue_*_official included
        assert (seeds / f"{name}.csv").read_text(encoding="utf-8") == "a,b\n", name
    for name in ["osm_sport_map", "all_racquet", "sport_aliases"]:                 # mapping seeds are kept
        assert (seeds / f"{name}.csv").read_text(encoding="utf-8").count("\n") == 3, name

    bad = [
        [["TX", "texas", "36.6", "-106.7", "25.8", "-93.5", "1"]],                # south above north
        [["TX", "Texas", "25.8", "-106.7", "36.6", "-93.5", "1"]],                # name must be lowercase
        [["TX", "texas", "25.8", "-106.7", "36.6", "-93.5", "abc"]],              # relation not a number
        [["TX", "texas", "25.8", "-106.7", "36.6", "-93.5", "1"], ["TX", "oklahoma", "33.6", "-103", "37", "-94.4", "2"]],  # duplicate code
    ]
    for specs in bad:
        try:
            f.parse_regions(specs)
        except SystemExit:
            continue
        raise AssertionError(f"accepted bad region {specs}")
    try:
        f.parse_metros([["x", "0", "0", "1", "1", "ZZ"]], regions)
    except SystemExit:
        pass
    else:
        raise AssertionError("accepted a metro with an unknown region code")
    print("init_fork: all cases ok")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
