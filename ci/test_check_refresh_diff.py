"""Offline test for the merge-gate classifier (ci/check_refresh_diff.py): synthetic exports, no git, no network.
A refresh-sized change must stay R0; a link swap, a bulk event rewrite or a new array must escalate. Run: python ci/test_check_refresh_diff.py"""
import copy, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ci"))
import check_refresh_diff as g  # noqa: E402


def export():
    return {
        "meta": {"venues": 1000},
        "sports": [{"n": f"Sport {i}", "u": {"l": f"https://example.org/sport/{i}"}} for i in range(10)],
        "venues": [{"i": f"v{i}", "n": f"Venue {i}", "w": f"https://venue{i}.example.org/", "ac": [["clinic", "Clinic", f"https://book.example.org/{i}"]]}
                   for i in range(1000)],
        "events": [{"n": f"Event {i}", "s": "2026-11-01", "u": f"https://events.example.org/{i}", "k": ""} for i in range(40)],
        "social": [{"n": f"Group {i}", "u": f"https://social.example.org/{i}", "g": f"https://social.example.org/{i}/join"} for i in range(20)],
        "walls": [{"n": f"Wall {i}", "wl": f"v{i}"} for i in range(100)],
        "platforms": [{"n": f"App {i}", "u": f"https://apps.example.org/{i}"} for i in range(10)],
    }


def reasons_for(mutate):
    old = export()
    new = copy.deepcopy(old)
    mutate(new)
    return g.classify_exports(old, new)[1]


def swap_websites(n):
    def f(d):
        for v in d["venues"][:n]:
            v["w"] = "https://evil.example.net/" + v["i"]
    return f


def swap_in_array(key, field, n):
    def f(d):
        for r in d[key][:n]:
            r[field] = "https://evil.example.net/x"
    return f


# no change, and an ordinary refresh (40 dates moved on 6 events, 3 venues renamed, 10 new venues, 2 gone): R0
assert reasons_for(lambda d: None) == []
def ordinary(d):
    for e in d["events"][:6]:
        e["s"] = "2026-12-01"
    for v in d["venues"][:3]:
        v["n"] += " (renamed)"
    d["venues"] = d["venues"][2:] + [{"i": f"new{i}", "n": "New", "w": f"https://new{i}.example.org/"} for i in range(10)]
    d["sports"][0]["v"] = 5   # a count follows the venues: sports rows are not row-capped
    for s in d["sports"]:
        s["v"] = 9
assert reasons_for(ordinary) == [], reasons_for(ordinary)

# gap 3: websites swapped on existing venues, under the 5% changed-field cap but over the URL cap (0.5% = 5 of 1000)
assert any("gained a URL" in r for r in reasons_for(swap_websites(6)))
assert reasons_for(swap_websites(5)) == []

# gap 2: events, social, platforms and sports were not diffed before
assert any("events" in r for r in reasons_for(swap_in_array("events", "u", 6)))
assert any("social" in r for r in reasons_for(swap_in_array("social", "g", 6)))
assert any("platforms" in r for r in reasons_for(swap_in_array("platforms", "u", 6)))
assert any("sports" in r and "new URLs" in r for r in reasons_for(lambda d: [s.__setitem__("u", {"l": "https://evil.example.net/" + s["n"]}) for s in d["sports"][:6]]))
assert any("events" in r and "rows" in r for r in reasons_for(lambda d: [e.__setitem__("n", "Rewritten") for e in d["events"][:10]]))  # 10 > 20% of 40 = 8
assert any("walls" in r for r in reasons_for(lambda d: [w.__setitem__("wl", "v999") for w in d["walls"][:25]]))

# a nested link-out URL (venue `ac`) counts the same as a website
def swap_link_out(d):
    for v in d["venues"][:6]:
        v["ac"][0][2] = "https://evil.example.net/book"
assert any("gained a URL" in r for r in reasons_for(swap_link_out))

# removing links is not a link swap; an unknown new array is caught as rows added
def drop_links(d):
    for v in d["venues"][:50]:
        v["w"] = ""
assert reasons_for(drop_links) == []
assert any("surprise" in r for r in reasons_for(lambda d: d.__setitem__("surprise", [{"n": i} for i in range(6)])))
print("check_refresh_diff: all cases ok")
