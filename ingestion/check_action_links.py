"""Check that every link-out in transform/seeds/venue_actions.csv still loads (HTTP 200 after redirects).

    python ingestion/check_action_links.py        (or: make check-links)

Run it before deploying and now and then: club sites reorganise their pages. Exits non-zero if any link fails.
Limits: it proves the page loads, not that its content still matches our note. BracketSync is a JavaScript app that answers
200 for any path, so its links can only be confirmed by opening them in a browser.
"""
from __future__ import annotations

import csv
import sys

import requests

SEED = "transform/seeds/venue_actions.csv"
UA = {"User-Agent": "courtconnect-ca/0.1 (link check; portfolio project)"}


def main() -> None:
    with open(SEED, encoding="utf-8", newline="") as f:
        urls = sorted({r["url"].strip() for r in csv.DictReader(f)})
    bad = 0
    for u in urls:
        try:
            r = requests.get(u, headers=UA, timeout=25, allow_redirects=True, stream=True)
            r.close()
            ok, status = r.status_code == 200, str(r.status_code)
        except requests.RequestException as err:
            ok, status = False, type(err).__name__
        bad += not ok
        print(f"{'OK ' if ok else 'BAD'} {status:>4}  {u}")
    print(f"\n{len(urls)} unique links, {bad} failing")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
