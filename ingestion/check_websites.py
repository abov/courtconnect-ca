"""Check whether the websites listed for our venues still exist, and record the result.

Why: in the open places dataset about 12% of listed websites no longer resolve, and the dataset's own confidence score does
not predict it (dead sites were rated 0.99-1.00). Showing a dead link to a player is a bad experience, so we flag it.

What it checks: a DNS lookup only. No page is fetched and no website is contacted, so it is cheap and polite.
What counts as dead: ONLY a definitive "this domain does not exist" answer, after trying both www.<domain> and <domain>.
Timeouts and temporary DNS failures are recorded as 'unknown', never 'dead', so a flaky network cannot mislabel a good site.
Limit: a domain that resolves may still show the wrong business (parked or resold domains); this does not catch that.

    python ingestion/check_websites.py                    # check anything not checked in the last 14 days
    python ingestion/check_websites.py --max-age-days 0   # re-check everything

Output: data/raw/website_checks.csv  (domain, status, resolved_host, checked_at)   status: ok | dead | unknown
"""
from __future__ import annotations

import argparse
import csv
import socket
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

import duckdb

FIELDS = ["domain", "status", "resolved_host", "checked_at"]
# Resolver answers that mean "this name does not exist" (Linux/macOS and Windows codes). Anything else is inconclusive.
_DEFINITIVE = {getattr(socket, "EAI_NONAME", -2), getattr(socket, "EAI_NODATA", -5), 11001, 11004}


def domain_of(url: str | None) -> str | None:
    """Normalise a website to its bare domain. MUST match the dbt macro website_domain() (macros/website.sql)."""
    if not url or not url.strip():
        return None
    u = url.strip()
    host = urlsplit(u if "//" in u else "http://" + u).hostname or ""
    host = host.lower().strip(".")
    if host.startswith("www."):
        host = host[4:]
    return host or None


def resolve(host: str) -> str:
    """'ok' | 'dead' | 'unknown' for one hostname."""
    try:
        socket.getaddrinfo(host, None)
        return "ok"
    except socket.gaierror as err:
        return "dead" if err.args and err.args[0] in _DEFINITIVE else "unknown"
    except OSError:
        return "unknown"


def check(domain: str) -> dict:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    outcomes = {}
    for host in (domain, "www." + domain):
        for attempt in range(2):                    # one retry, so a blip is not a verdict
            outcomes[host] = resolve(host)
            if outcomes[host] != "unknown":
                break
            time.sleep(1.5)
        if outcomes[host] == "ok":
            return {"domain": domain, "status": "ok", "resolved_host": host, "checked_at": now}
    status = "dead" if all(v == "dead" for v in outcomes.values()) else "unknown"
    return {"domain": domain, "status": status, "resolved_host": "", "checked_at": now}


def collect_domains(db: str) -> set[str]:
    con = duckdb.connect(db, read_only=True)
    urls = [r[0] for r in con.execute("select website from raw.overture_places where website is not null").fetchall()]
    urls += [r[0] for r in con.execute("select website from raw.osm_courts where website is not null").fetchall()]
    if _has(con, "raw", "manual_venues"):               # a dbt seed, so it exists once `dbt build` has run
        urls += [r[0] for r in con.execute("select website from raw.manual_venues where website is not null").fetchall()]
    return {d for d in (domain_of(u) for u in urls) if d}


def _has(con, schema: str, table: str) -> bool:
    return con.execute("select count(*) from information_schema.tables where table_schema=? and table_name=?",
                       [schema, table]).fetchone()[0] > 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="courtconnect.duckdb")
    ap.add_argument("--out", default="data/raw/website_checks.csv")
    ap.add_argument("--max-age-days", type=int, default=14, help="skip domains checked more recently than this")
    ap.add_argument("--workers", type=int, default=24)
    args = ap.parse_args()

    out = Path(args.out)
    previous: dict[str, dict] = {}
    if out.exists():
        with out.open(encoding="utf-8", newline="") as f:
            previous = {r["domain"]: r for r in csv.DictReader(f)}
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.max_age_days)

    def fresh(r: dict) -> bool:
        try:
            return datetime.fromisoformat(r["checked_at"]) > cutoff and r["status"] != "unknown"
        except (KeyError, ValueError):
            return False

    domains = sorted(collect_domains(args.db))
    todo = [d for d in domains if not (d in previous and fresh(previous[d]))]
    print(f"{len(domains):,} distinct website domains; {len(todo):,} to check ({len(domains) - len(todo):,} fresh)")

    socket.setdefaulttimeout(5)
    with ThreadPoolExecutor(args.workers) as ex:
        results = list(ex.map(check, todo))
    merged = {**previous, **{r["domain"]: r for r in results}}
    merged = {d: r for d, r in merged.items() if d in set(domains)}      # drop domains no longer used anywhere

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(sorted(merged.values(), key=lambda r: r["domain"]))
    counts = {s: sum(1 for r in merged.values() if r["status"] == s) for s in ("ok", "dead", "unknown")}
    print(f"Wrote {len(merged):,} rows to {out}:  ok {counts['ok']:,}   dead {counts['dead']:,}   unknown {counts['unknown']:,}")


if __name__ == "__main__":
    main()
