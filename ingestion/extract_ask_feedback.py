"""Pull the questions visitors chose to send from the ask box ("Send this question to us") out of the GoatCounter export.

    python ingestion/extract_ask_feedback.py      # after extract_goatcounter.py; writes ask_feedback.csv in the shared raw folder
    python ingestion/load_raw.py                  # -> raw.ask_feedback, then dbt: stg_ask_feedback, mart_ask_feedback

Only questions sent with the button arrive (event path event/ask-feedback/<slug>, the scrubbed text is the title). The text is scrubbed
again here (emails, links, phone-like numbers) so an old or hand-made hit can't carry them. The CSV stays in the raw folder and the local
warehouse: never commit it, and never copy it into docs/ or the dashboard (the repo is public). GoatCounter only keeps 60 days per export,
so a refreshed day replaces its old rows and older days stay.
"""
from __future__ import annotations

import csv
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from rawdir import raw_path  # noqa: E402

PREFIX = "event/ask-feedback/"
COLS = ["day", "question", "count"]


def scrub(text: str) -> str:
    """Same rules as Ask.scrub in app/ask.js."""
    t = re.sub(r"[^\s@]+@[^\s@]+", "[email]", text or "")
    t = re.sub(r"(https?://|www\.)\S+", "[link]", t, flags=re.I)
    t = re.sub(r"\+?\d[\d\s().-]{6,}\d", "[number]", t)
    return re.sub(r"\s+", " ", t).strip()[:200]


def questions(rows) -> dict[tuple[str, str], int]:
    """GoatCounter export rows -> {(day, question): count}. The title is the question; the path slug is the fallback."""
    out: dict[tuple[str, str], int] = defaultdict(int)
    for r in rows:
        path = r["path"].lstrip("/")
        if r["is_event"].lower() != "true" or not path.startswith(PREFIX):
            continue
        q = scrub(r["title"] if r["title"] and r["title"] != path else path[len(PREFIX):].replace("-", " "))
        if len(q) >= 3:
            out[(r["day"], q)] += int(r["count"])
    return out


def main() -> None:
    src, out = Path(raw_path("goatcounter_daily.csv")), Path(raw_path("ask_feedback.csv"))
    if not src.exists():
        sys.exit(f"{src} not found: run ingestion/extract_goatcounter.py first.")
    with src.open(encoding="utf-8") as f:
        rows_in = list(csv.DictReader(f))
    fresh = questions(rows_in)
    covered = {r["day"] for r in rows_in}   # every day in the export replaces its old rows, even a day with no feedback now
    kept: dict[tuple[str, str], int] = {}
    if out.exists():
        with out.open(encoding="utf-8", newline="") as f:
            kept = {(r["day"], r["question"]): int(r["count"]) for r in csv.DictReader(f) if r["day"] not in covered}
    kept.update(fresh)
    rows = sorted((d, q, c) for (d, q), c in kept.items())
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        w.writerows(rows)
    print(f"{len(fresh)} question rows in this export, {len(rows)} in total -> {out}")


if __name__ == "__main__":
    main()
