"""Check the docs hub (docs/README.md): every doc in docs/ is listed, and every local link in the hub resolves.
Keeps the single entry point from drifting: add a doc, add its line to the hub in the same PR."""
import re
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / "docs"
hub = (DOCS / "README.md").read_text(encoding="utf-8")
links = re.findall(r"\]\(([^)\s]+)\)", hub)
local = [l.split("#")[0] for l in links if not l.startswith(("http", "#", "mailto:")) and l.split("#")[0]]

errors = []
for target in local:
    if not (DOCS / target).exists():
        errors.append(f"broken link in docs/README.md: {target}")
listed = {Path(t).as_posix() for t in local}
for md in sorted(DOCS.glob("*.md")):
    if md.name != "README.md" and md.name not in listed:
        errors.append(f"docs/{md.name} is not listed in docs/README.md")
if errors:
    print("docs hub check FAILED:")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print(f"docs hub: {len(local)} local links resolve, all {len(list(DOCS.glob('*.md'))) - 1} docs listed")
