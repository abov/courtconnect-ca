"""Check that the project pages share one nav bar (app/site-nav.css) and each marks its own page as current.
The nav is plain HTML repeated in each page so it works with no script; this keeps the copies identical apart from aria-current."""
import re
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app"
PAGES = {"how-its-built.html": "how-its-built.html", "run-history.html": "run-history.html", "ask-the-data.html": "ask-the-data.html"}
NAV = re.compile(r'<nav class="site-nav".*?</nav>', re.S)
CURRENT = re.compile(r' aria-current="page"')

errors, shapes = [], {}
for page, own in PAGES.items():
    html = (APP / page).read_text(encoding="utf-8")
    m = NAV.search(html)
    if not m:
        errors.append(f"{page}: no <nav class=\"site-nav\">")
        continue
    nav = m.group(0)
    if 'href="site-nav.css"' not in html:
        errors.append(f"{page}: does not link site-nav.css")
    cur = re.findall(r'<a href="([^"]+)"[^>]*aria-current="page"', nav)
    if cur != [own]:
        errors.append(f"{page}: aria-current should be on {own}, found {cur}")
    shapes[page] = CURRENT.sub("", nav)
if len(set(shapes.values())) > 1:
    errors.append("the nav differs between pages (beyond aria-current): " + ", ".join(shapes))
for href in re.findall(r'<a href="([^"#]+)', next(iter(shapes.values()), "")):
    if not href.startswith("http") and not (APP / href.split("?")[0]).exists() and href != "./" and href != "dashboard/":
        errors.append(f"nav link target missing in app/: {href}")
if not (APP / "site-nav.css").exists():
    errors.append("app/site-nav.css is missing")
if errors:
    print("site-nav check FAILED:")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print(f"site-nav: {len(PAGES)} pages share one nav")
