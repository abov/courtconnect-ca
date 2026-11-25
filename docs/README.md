# RacketConnect project hub

One free map of every racket sport, from park courts to private clubs. Pick the door that fits you.

**To update:** this page stays short on purpose. Every other doc, runbook and tool is listed in [`all_docs.md`](all_docs.md) (web copy: <https://abov.github.io/courtconnect-ca/all-docs.html>). Edit either file, then run `make hub` (`ingestion/build_hub_page.py`); `ci/check_docs_hub.py` fails CI if a doc in `docs/` is in neither list, a link is broken or a web copy is stale.

## 1. Use it

For players. Nothing to install, no sign-in.

- [Open the live map](https://abov.github.io/courtconnect-ca/): find a court, an event to watch or a group to play with.
- [Ask the data](https://abov.github.io/courtconnect-ca/ask-the-data.html): ask a plain-English question about the venues.
- Something wrong or missing? Use "Fix or add your listing" in the map's About card, or see [how to contribute](../CONTRIBUTING.md).

## 2. See how it's built

For reviewers and hiring managers: the whole story in about five minutes.

1. [How it's built](https://abov.github.io/courtconnect-ca/how-its-built.html): the pipeline, its checks and live numbers.
2. [Case study](case_study.md): the problem, trade-offs, incidents and results.
3. [Architecture](architecture.md): the layers and how data flows, in one diagram.
4. [Data quality dashboard](https://abov.github.io/courtconnect-ca/dashboard/): freshness, coverage and service levels, live.
5. [Decision records](decisions): one short record per design decision.

## 3. Run it

For whoever maintains the project.

- [All docs and tools](https://abov.github.io/courtconnect-ca/all-docs.html): every runbook, monitor, plan and research note, with a search box.
- [Project README](../README.md): quick start and how to edit the data. Then the [twice-monthly refresh](monthly_refresh.md).
- [Status](status.md): what is being worked on now.
