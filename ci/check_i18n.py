"""Guard rail for app/i18n/strings.json (the UI translations; machine-drafted, English is the key).

Fails when: the file is not valid JSON or repeats a key; a row does not have one non-empty text per language in `_langs`; a translation's {placeholders}
differ from the English key's; a key no longer appears in app/index.html (stale after the English text changed); or a literal t("...") / tn("...", "...")
in index.html has no row (it would silently stay English). Run from the repo root: python ci/check_i18n.py
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = (ROOT / "app" / "index.html").read_text(encoding="utf-8")
PH = re.compile(r"\{(\w+)\}")


def pairs(items):
    d = {}
    for k, v in items:
        if k in d:
            raise ValueError(f"duplicate key: {k[:70]}")
        d[k] = v
    return d


def squash(s):
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def main():
    errors = []
    try:
        data = json.loads((ROOT / "app" / "i18n" / "strings.json").read_text(encoding="utf-8"), object_pairs_hook=pairs)
    except ValueError as e:
        print("strings.json:", e)
        return 1
    langs = data["_langs"]
    rows = {k: v for k, v in data.items() if not k.startswith("_")}
    plain = squash(re.sub(r"<[^>]+>", "\n", PAGE))   # static text, tags removed
    js = PAGE.replace('\\"', '"')
    built = {"{n} " + w for call in re.findall(r'countWord\(\w+, "(\w+)", "(\w+)"\)', PAGE) for w in call}   # keys assembled in countWord()
    for k, v in rows.items():
        if not isinstance(v, list) or len(v) != len(langs) or not all(isinstance(x, str) and x.strip() for x in v):
            errors.append(f"needs {len(langs)} non-empty texts: {k[:70]}")
            continue
        want = sorted(PH.findall(k))
        for lang, text in zip(langs, v):
            if sorted(PH.findall(text)) != want:
                errors.append(f"[{lang}] placeholders differ from the key: {k[:70]}")
        if k not in built and k not in js and squash(k) not in plain and html.escape(k, quote=False) not in PAGE:
            errors.append(f"stale (not in index.html): {k[:70]}")
    # literal keys used in code: t("..."), tn(n, "one", "many"), richTn(n, "one", "many"), countWord(n, "one", "many")
    used = set(re.findall(r'\bt\("((?:[^"\\]|\\.)*)"', PAGE))
    for one, many in re.findall(r'\b(?:tn|richTn)\([^"]*?"((?:[^"\\]|\\.)*)",\s*"((?:[^"\\]|\\.)*)"', PAGE):
        used.update((one, many))
    for k in sorted(used):
        k = k.replace('\\"', '"')
        if k not in rows and not k.startswith("{n} "):
            errors.append(f"used in code but no row: {k[:70]}")
    if errors:
        print("\n".join(errors[:60]))
        print(f"{len(errors)} problem(s)")
        return 1
    print(f"ok: {len(rows)} strings x {len(langs)} languages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
