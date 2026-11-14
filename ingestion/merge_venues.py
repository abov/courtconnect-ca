"""Git merge driver for app/data/venues.json (one record per line; see dump_lines in export_app_data.py).

Git merges the record lines itself. Line 1 holds the `meta` object, whose counts (and the date) change in nearly every PR,
so it would conflict every time. This driver blanks that line, lets git merge the rest, then rebuilds meta:
numbers = ours + theirs - base, `generated` = the later date. The result is a good merge, not a regeneration:
still run `make app-data` after a full build before shipping (CI's ci/check_export_fresh.py checks it).

Set up once per clone: python ingestion/setup_git.py.  Called by git as: merge_venues.py %O %A %B (base, ours, theirs).
Exit 0 = merged cleanly into %A; exit 1 = real conflict (git leaves markers: take main's copy and rebuild, as before).
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

PLACEHOLDER = '{"meta":null,'
PREFIX = '{"meta":'


def split_meta(path):
    text = Path(path).read_text(encoding="utf-8")
    first, sep, rest = text.partition("\n")
    if not first.startswith(PREFIX) or not first.endswith(","):
        raise ValueError(f"{path}: line 1 is not the meta line (old minified layout? regenerate with make app-data)")
    return json.loads(first[len(PREFIX):-1]), PLACEHOLDER + sep + rest


def main(base, ours, theirs):
    try:
        mb, tb = split_meta(base)
        mo, to = split_meta(ours)
        mt, tt = split_meta(theirs)
    except (ValueError, OSError) as e:
        print(f"merge_venues: {e}", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        fb, fo, ft = (Path(tmp) / n for n in ("base", "ours", "theirs"))
        fb.write_text(tb, encoding="utf-8", newline="")
        fo.write_text(to, encoding="utf-8", newline="")
        ft.write_text(tt, encoding="utf-8", newline="")
        if subprocess.run(["git", "merge-file", str(fo), str(fb), str(ft)]).returncode != 0:
            return 1
        merged = fo.read_text(encoding="utf-8")
    meta = dict(mo)
    for k, v in mo.items():
        if isinstance(v, int) and not isinstance(v, bool):
            meta[k] = v + mt.get(k, v) - mb.get(k, v)
    meta["generated"] = max(mo.get("generated", ""), mt.get("generated", ""))
    line1 = PREFIX + json.dumps(meta, ensure_ascii=False, separators=(",", ":")) + ","
    out = line1 + merged[len(PLACEHOLDER):]
    try:
        json.loads(out)
    except ValueError as e:
        print(f"merge_venues: merged file is not valid JSON ({e})", file=sys.stderr)
        return 1
    Path(ours).write_text(out, encoding="utf-8", newline="")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
