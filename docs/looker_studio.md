# Looker Studio report (second BI view)

A free Google Looker Studio report over the same aggregates as the [Evidence.dev dashboard](../dashboard/README.md). Two tools on one set of numbers shows the data is not tied to one vendor. Only counts and dates are used: no venue rows, addresses or contacts.

## Data source
A private Google Sheet, "RacketConnect dashboard data (aggregates only)", in the owner's Drive, with three tabs that match `make dashboard-data`:

| Tab | Source CSV | Use |
|---|---|---|
| `trend` | `dashboard/sources/courtconnect/trend.csv` | one row per refresh: venues, name %, SLAs, tests |
| `stats` | `stats.csv` | one row: latest build numbers |
| `sport_coverage` | `sport_coverage.csv` | venues per sport and coverage status |

Looker Studio cannot read a CSV from a URL, which is why the Sheet sits in between.

## Refresh (twice a month, after `make quality`, `make stats`, `make app-data`)
1. `make dashboard-data` (or `python ingestion/export_dashboard_data.py`).
2. In the Sheet, File > Import > Replace current sheet for each tab with its CSV. (Or ask Claude to write the three tabs.)
3. Looker Studio re-reads the Sheet by itself (it caches for a while; the report's refresh button forces it).

## Report layout
Page 1, "Scorecard": scorecard tiles for `venues`, `sports_with_venues`, `named_pct`, `sla_met / sla_total`, `tests_pass` (from `stats`); a time series of `venues` and `named_pct` by `date` (from `trend`); a table of the SLA columns.
Page 2, "Sport coverage": a bar chart of `venues` by `sport` (sort descending, top 25), a donut of sport count by `status`, and a filter control on `status`. Note on the page that sports inferred as also played on tennis courts are labelled inferred on the map.
Match the Evidence palette: blue `#1F5FA8`, gold `#F2B134`, teal `#0a7d6e`.

## Sharing
Share the report as "Anyone with the link can view", never the Sheet. Put the report link in the README only once the owner has published it. Do not embed the report in the map page: Looker Studio loads Google scripts and cookies, which the map's privacy stance (only GoatCounter for usage counts) avoids.
