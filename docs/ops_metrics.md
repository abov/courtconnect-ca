# Delivery and workflow metrics (`make ops-metrics`, added 2026-11-14)

Answers "what is slowing the project down?" with data the other monitors do not hold. Read-only: it prints a report and writes nothing, so there is no generated file to go stale. Needs `gh` logged in for the first two sections. Elementary ([`data_observability.md`](data_observability.md)) covers data health; this covers delivery and cost.

```bash
python ingestion/ops_metrics.py                         # last 14 days, all sections (about 5 min: one gh call per merged PR, plus session logs)
python ingestion/ops_metrics.py --days 7 --only runs    # sections: prs, runs, build, tokens
```

## What each section answers
- **prs**: merged PRs per day, how many carried a merge-of-main, rebase, conflict or "regenerate `venues.json`" commit, how many touched `venues.json`, median minutes open.
- **runs**: per workflow (ci, pages, merge gate, PR unstick): runs, failures, cancellations, median/p90/max minutes, failed runs per day, and the slowest steps of the latest successful ci and pages runs.
- **build**: slowest dbt nodes of the last local invocation (`transform/target/run_results.json`).
- **tokens**: per day and per session, from this machine's Claude Code logs: fresh input, cache re-reads, output, peak context per session, and which tools return the most text into context.

## First reading (2026-11-07 to 2026-11-14)
- **Conflicts:** 42 of 100 merged PRs needed a merge, rebase or regenerate commit; most of those also touched `venues.json`, the one generated file every PR collides on.
- **CI is not the bottleneck:** ci median 1.3 min, pages 2.7 min, 11 failures in 214 ci runs. The `venues.json` rebuild-after-rebase loop costs more than any workflow.
- **Local dbt:** a full build is about 2 min; `stg_osm_courts`, `int_venue_pairs_15mi` and Elementary's on-run-end hook are the slowest nodes.
- **Tokens:** cache re-reads dominate (hundreds of millions per day); the heaviest sessions peaked at 200-330k context, past the fresh-session point in `CLAUDE.md`.

## Limits
- GitHub does not record conflicts. The signal is inferred from commit messages (`CONFLICT_RE` in the script) and can over- or under-count.
- Token counts come from local session logs on the machine that ran the sessions; cloud routines and other machines are not included. Cost in dollars is not computed.
- The PR list is capped at 100 and the Actions list at 500 runs.
