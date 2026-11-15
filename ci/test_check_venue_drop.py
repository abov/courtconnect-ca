"""Offline test for ci/check_venue_drop.py: the 2026-11-15 drop is caught, normal changes pass."""
import sys
sys.path.insert(0, "ci")
from collections import Counter
from check_venue_drop import counts, drops

old = Counter({"CA": 10065, "TX": 5526, "AZ": 2096, "NM": 532, "NV": 547, "HI": 452, "XX": 10})
bad = Counter({"CA": 10064, "TX": 185, "AZ": 164, "NM": 50, "NV": 547, "HI": 76})
assert len(drops(old, bad)) == 5, drops(old, bad)   # total + TX, AZ, NM, HI (XX is under 50 venues: ignored)
assert not drops(old, Counter({"CA": 10100, "TX": 5400, "AZ": 2096, "NM": 532, "NV": 547, "HI": 452, "XX": 0}))
assert counts('{"meta":{}}\n{"i":"a","r":"CA"},\n{"i":"b"}\n"sports":[\n')["CA"] == 1
print("check_venue_drop: ok")
