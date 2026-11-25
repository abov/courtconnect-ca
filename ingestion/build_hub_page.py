"""Write the web copies of the project hub: app/hub.html (docs/README.md, three short doors: use it, see how it's built,
run it) and app/all-docs.html (docs/all_docs.md, every doc and tool, with a search box).

The two markdown files stay the only lists anyone edits; this turns them into HTML with no extra library (they use only
headings, paragraphs, lists, tables, links, `code` and **bold**). Doc links open on GitHub; live-site links become
relative so they work locally too. A "**To update:**" paragraph goes to the page footer. `--check` exits 1 when a web
copy is stale (ci/check_docs_hub.py runs it).
Usage: python ingestion/build_hub_page.py [--check]
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = ROOT / "app" / "hub.html"
# (source in docs/, output in app/, <title>, meta description, search box, sections drawn as cards)
PAGES = [
    ("README.md", "hub.html", "RacketConnect project hub",
     "RacketConnect in three doors: use the map, see how it is built, or run it.", False, True),
    ("all_docs.md", "all-docs.html", "RacketConnect: all docs and tools",
     "Every RacketConnect doc, runbook, monitor and tool, grouped by purpose.", True, False),
]
REPO = "https://github.com/abov/courtconnect-ca"
SITE = "https://abov.github.io/courtconnect-ca/"


def slug(text):
    """GitHub-style heading id, so old #anchors into docs/README.md work on the page too."""
    return re.sub(r"\s", "-", re.sub(r"[^\w\s-]", "", text.lower()).strip())


def href(url):
    if url.startswith(SITE):
        return url[len(SITE):] or "./"
    if url.startswith(("http", "mailto:", "#")):
        return url
    path, _, frag = url.partition("#")
    target = (DOCS / path).resolve()
    rel = target.relative_to(ROOT).as_posix()
    kind = "tree" if target.is_dir() else "blob"
    if rel.startswith("app/") and not rel.endswith(".md") and (ROOT / rel).is_file():
        return rel[len("app/"):]  # served by the site itself (llms.txt)
    return f"{REPO}/{kind}/main/{rel}" + (f"#{frag}" if frag else "")


def inline(text):
    codes = []

    def keep(m):
        codes.append(f"<code>{html.escape(m.group(1), quote=False)}</code>")
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", keep, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: f'<a href="{html.escape(href(m.group(2)))}">{m.group(1)}</a>', text)
    text = re.sub(r"&lt;(https?://[^\s&]+)&gt;", lambda m: f'<a href="{html.escape(href(m.group(1)))}">{m.group(1).split("://", 1)[1].rstrip("/")}</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], text)


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def convert(md, doors=False):
    """Returns (title, lede, body html, table of contents, footer note). doors=True wraps each ## section in a card."""
    lines = md.splitlines()
    title = lines[0].lstrip("# ").strip()
    out, toc, i = [], [], 1
    lede, note, in_door = None, "", False
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
        elif line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            text = line[level:].strip()
            if level == 2:
                toc.append((slug(text), re.sub(r"^\d+\.\s*", "", text)))
                if doors:
                    out.append(("</section>" if in_door else "") + '<section class="door">')
                    in_door = True
            out.append(f'<h{level} id="{slug(text)}">{inline(text)}</h{level}>')
            i += 1
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(cells(lines[i]))
                i += 1
            head, body = rows[0], [r for r in rows[1:] if not all(set(c) <= set("-: ") for c in r)]
            out.append('<div class="tbl"><table><thead><tr>' + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body) + "</tbody></table></div>")
        elif re.match(r"(- |\d+\. )", line):
            tag = "ol" if line[0].isdigit() else "ul"
            items = []
            while i < len(lines) and re.match(r"(- |\d+\. )", lines[i]):
                items.append(re.sub(r"^(- |\d+\. )", "", lines[i]))
                i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{inline(t)}</li>" for t in items) + f"</{tag}>")
        else:
            para = []
            while i < len(lines) and lines[i].strip() and not re.match(r"(#|\||- |\d+\. )", lines[i]):
                para.append(lines[i].strip())
                i += 1
            text = inline(" ".join(para))
            if lede is None and not out:
                lede = text
            elif para[0].startswith("**To update"):
                note = text
            else:
                out.append(f"<p>{text}</p>")
    if in_door:
        out.append("</section>")
    return title, lede or "", "\n".join(out), toc, note


NAV = """<nav class="site-nav" aria-label="RacketConnect pages">
      <a href="./">Map</a>
      <a href="how-its-built.html">How it&rsquo;s built</a>
      <a href="dashboard/">Data quality</a>
      <a href="hub.html" aria-current="page">Hub</a>
      <a href="run-history.html">Run history</a>
      <a href="ask-the-data.html">Ask the data</a>
      <a href="https://github.com/abov/courtconnect-ca">Source</a>
    </nav>"""

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<!-- Generated by ingestion/build_hub_page.py from docs/__SRC__. Do not edit here: edit docs/__SRC__ and rerun the script. -->
<title>__PAGETITLE__</title>
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="icon" href="favicon.png" type="image/png" sizes="64x64">
<link rel="apple-touch-icon" href="icon-180.png">
<meta name="theme-color" content="#fbfaf7" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#10151c" media="(prefers-color-scheme: dark)">
<meta name="description" content="__DESC__">
<link rel="canonical" href="https://abov.github.io/courtconnect-ca/__OUT__">
<style>
  /* Same tokens and fonts as how-its-built.html so the pages read as one site. No cookies, no third-party requests. */
  @font-face { font-family: "Plus Jakarta Sans"; font-style: normal; font-weight: 500 800; font-display: swap; src: url(fonts/plus-jakarta-sans-latin.woff2) format("woff2"); }
  :root {
    --font-body: system-ui, -apple-system, "Segoe UI Variable Text", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    --font-head: "Plus Jakarta Sans", var(--font-body);
    --bg: #fbfaf7; --panel: #ffffff; --text: #1f2328; --muted: #59636e; --line: #d6d1c4; --accent: #1F5FA8; --on-accent: #ffffff;
    --hi: #F2B134; --tint: #e6eefa; --r-md: 12px;
  }
  @media (prefers-color-scheme: dark) {
    :root { --bg: #10151c; --panel: #171e27; --text: #e6edf3; --muted: #9aa3ad; --line: #3a424d; --accent: #6aa5ee; --on-accent: #0d1117; --tint: #1b3556; }
  }
  * { box-sizing: border-box; }
  body { margin: 0; font: 16px/1.6 var(--font-body); color: var(--text); background: var(--bg); }
  a { color: var(--accent); }
  a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 2px; }
  header { border-bottom: 3px solid var(--hi); background: linear-gradient(180deg, color-mix(in srgb, var(--hi) 16%, var(--panel)), var(--panel)); }
  .wrap { max-width: 860px; margin: 0 auto; padding: 0 16px; }
  header .wrap { padding-top: 14px; padding-bottom: 18px; }
  h1, h2, h3 { font-family: var(--font-head); letter-spacing: -.015em; line-height: 1.25; }
  h1 { font-size: clamp(26px, 6vw, 34px); font-weight: 800; margin: 10px 0 6px; color: var(--accent); }
  h2 { font-size: 21px; font-weight: 700; margin: 36px 0 6px; scroll-margin-top: 12px; }
  h3 { font-size: 16px; font-weight: 700; margin: 20px 0 4px; }
  .lede { font-size: 17px; color: var(--muted); margin: 0; max-width: 62ch; }
  main { padding-bottom: 48px; }
  p { margin: 8px 0; max-width: 72ch; }
  .meta { color: var(--muted); font-size: 13.5px; }
  ul, ol { padding-left: 22px; margin: 8px 0; }
  li { margin: 5px 0; max-width: 72ch; }
  code { font: 13.5px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; background: var(--tint); padding: 1px 5px; border-radius: 4px; overflow-wrap: anywhere; }
  .tbl { overflow-x: auto; margin: 10px 0; border: 1px solid var(--line); border-radius: var(--r-md); background: var(--panel); }
  table { border-collapse: collapse; width: 100%; font-size: 15px; }
  th, td { text-align: left; vertical-align: top; padding: 8px 12px; border-top: 1px solid var(--line); }
  thead th { border-top: 0; font-size: 13px; color: var(--muted); font-weight: 600; }
  td a { overflow-wrap: anywhere; }
  .jump { display: flex; flex-wrap: wrap; gap: 8px; margin: 18px 0 0; padding: 0; list-style: none; }
  .jump a { display: inline-block; padding: 5px 12px; border: 1px solid var(--line); border-radius: 999px; background: var(--panel); text-decoration: none; font-size: 14px; }
  .jump a:hover { background: var(--tint); }
  .find { margin: 18px 0 0; }
  .find input { width: 100%; max-width: 420px; font: inherit; padding: 8px 12px; border: 1px solid var(--line); border-radius: 8px; background: var(--panel); color: var(--text); }
  .find small { display: block; color: var(--muted); font-size: 13px; margin-top: 4px; min-height: 1.4em; }
  .hide { display: none; }
  .door { margin: 22px 0; padding: 4px 20px 14px; border: 1px solid var(--line); border-radius: var(--r-md); background: var(--panel); }
  .door h2 { margin-top: 14px; }
  .door > p:first-of-type { color: var(--muted); margin-top: 0; }
  footer { border-top: 1px solid var(--line); padding: 16px 0 28px; font-size: 13.5px; color: var(--muted); }
</style>
<link rel="stylesheet" href="site-nav.css">
</head>
<body>
<header>
  <div class="wrap">
    __NAV__
    <h1>__TITLE__</h1>
    <p class="lede">__LEDE__</p>
    <ul class="jump" aria-label="Sections">__TOC__</ul>
__FIND__  </div>
</header>

<main class="wrap">
__BODY__
</main>

<footer>
  <div class="wrap">__NOTE__This page is generated from <a href="https://github.com/abov/courtconnect-ca/blob/main/docs/__SRC__">docs/__SRC__</a>. It sets no cookies and requests nothing from other sites.</div>
</footer>
__SCRIPT__<script>
// Filter: hides list items and table rows that do not contain every typed word; headings stay.
(function () {
  var q = document.getElementById("q"), qn = document.getElementById("qn");
  var items = Array.prototype.slice.call(document.querySelectorAll("main li, main tbody tr, main p"));
  q.addEventListener("input", function () {
    var words = q.value.toLowerCase().split(/\\s+/).filter(Boolean), shown = 0;
    items.forEach(function (el) {
      var hit = words.every(function (w) { return el.textContent.toLowerCase().indexOf(w) >= 0; });
      el.classList.toggle("hide", !hit);
      if (hit) shown++;
    });
    document.querySelectorAll("main .tbl").forEach(function (t) { t.classList.toggle("hide", !t.querySelector("tbody tr:not(.hide)")); });
    qn.textContent = words.length ? shown + " match" + (shown === 1 ? "" : "es") : "";
  });
})();
</script>
SCRIPT_END</body>
</html>
"""


FIND = """    <div class="find"><label for="q" class="meta">Find a page, doc or tool</label><br><input id="q" type="search" placeholder="e.g. refresh, padel, costs, uptime" autocomplete="off"><small id="qn" aria-live="polite"></small></div>
"""


def render(src="README.md"):
    """The HTML for one source file in PAGES (default: the hub)."""
    _, out, page_title, desc, search, doors = next(p for p in PAGES if p[0] == src)
    title, lede, body, toc, note = convert((DOCS / src).read_text(encoding="utf-8"), doors)
    jump = "".join(f'<li><a href="#{s}">{html.escape(t)}</a></li>' for s, t in toc)
    head, script = PAGE.split("__SCRIPT__")
    script, tail = script.split("SCRIPT_END")
    page = head + (script if search else "") + tail
    return (page.replace("__NAV__", NAV).replace("__TITLE__", html.escape(title)).replace("__LEDE__", lede)
            .replace("__TOC__", jump).replace("__BODY__", body).replace("__FIND__", FIND if search else "")
            .replace("__NOTE__", note + " " if note else "").replace("__SRC__", src).replace("__OUT__", out)
            .replace("__PAGETITLE__", html.escape(page_title)).replace("__DESC__", html.escape(desc)))


def stale():
    """Web copies that do not match their source, as app/ paths."""
    return [f"app/{out}" for src, out, *_ in PAGES
            if not (ROOT / "app" / out).exists() or (ROOT / "app" / out).read_text(encoding="utf-8") != render(src)]


if __name__ == "__main__":
    if "--check" in sys.argv:
        bad = stale()
        if bad:
            print(f"{', '.join(bad)} stale: run python ingestion/build_hub_page.py and commit")
            sys.exit(1)
        print("app/hub.html and app/all-docs.html match their sources")
    else:
        for src, out, *_ in PAGES:
            (ROOT / "app" / out).write_text(render(src), encoding="utf-8", newline="\n")
            print(f"wrote app/{out}")
