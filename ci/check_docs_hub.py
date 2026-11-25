"""Check the docs hub: docs/README.md (the short hub) plus docs/all_docs.md (every doc and tool) list every doc in docs/,
every local link in them resolves, and their web copies (app/hub.html, app/all-docs.html) are current.
Keeps the entry points from drifting: add a doc, add its line to all_docs.md in the same PR."""
import re
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / "docs"
LISTS = ("README.md", "all_docs.md")
hub = "\n".join((DOCS / name).read_text(encoding="utf-8") for name in LISTS)
links = re.findall(r"\]\(([^)\s]+)\)", hub)
local = [l.split("#")[0] for l in links if not l.startswith(("http", "#", "mailto:")) and l.split("#")[0]]

errors = []
for target in local:
    if not (DOCS / target).exists():
        errors.append(f"broken link in docs/README.md or docs/all_docs.md: {target}")
listed = {Path(t).as_posix() for t in local}
for md in sorted(DOCS.glob("*.md")):
    if md.name not in LISTS and md.name not in listed:
        errors.append(f"docs/{md.name} is not listed in docs/all_docs.md")
# Drift guards: every `make <target>` the hub names must exist, and every live-site page that README.md or the app nav names must be in the hub.
ROOT = DOCS.parent
makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
targets = set(re.findall(r"^([a-z][\w-]*):", makefile, re.M))
for t in sorted(set(re.findall(r"`make ([a-z][\w-]*)", hub))):
    if t not in targets:
        errors.append(f"the hub names `make {t}` but the Makefile has no such target")
SITE = "https://abov.github.io/courtconnect-ca/"
hub_pages = {u.rstrip("/") for u in re.findall(r"https://abov\.github\.io/courtconnect-ca/[^\s)>|\"']*", hub)}
for src in (ROOT / "README.md",):
    for u in re.findall(r"https://abov\.github\.io/courtconnect-ca/[^\s)>|\"']*", src.read_text(encoding="utf-8")):
        page = u.split("#")[0].rstrip("/")
        if page not in hub_pages and page != SITE.rstrip("/") + "/how-its-built.html" and page != SITE.rstrip("/"):
            errors.append(f"{src.name} links {page}, which is in neither docs/README.md nor docs/all_docs.md")
# The web copies (app/hub.html, app/all-docs.html) must match their sources.
sys.path.insert(0, str(ROOT / "ingestion"))
from build_hub_page import stale  # noqa: E402
for page in stale():
    errors.append(f"{page} is stale: run python ingestion/build_hub_page.py and commit it")
if errors:
    print("docs hub check FAILED:")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print(f"docs hub: {len(local)} local links resolve, all {len(list(DOCS.glob('*.md'))) - len(LISTS)} docs listed")
