# Dashboard prototype (Evidence.dev)

A one-page BI-as-code scorecard: service-level numbers, venue and name-quality trends, and sport coverage. Markdown plus SQL, built to a static site. **Local prototype only: it is not wired into `pages.yml` or CI.**

## Run it
```bash
make quality && make stats && make app-data    # the numbers it reads
make dashboard-data                            # copies aggregates to dashboard/sources/courtconnect/*.csv (git-ignored)
cd dashboard
npm install            # once; Node 18+ (built and tested on Node 26.13, npm 11.20)
npm run sources        # load the CSVs
npm run build          # static site in dashboard/build
python -m http.server 8766 --directory build   # open http://localhost:8766
```
`npm run dev` gives live reload. Keep the dev server on localhost only (see "Known risks").

## What it reads
Only aggregates: `docs/data_quality_trend.csv`, `app/data/build_stats.json` and per-sport venue counts from `app/data/venues.json`. No venue rows, addresses or contacts; the warehouse is never opened. `ingestion/export_dashboard_data.py` writes the CSVs.

## Why the community edition, pinned
Evidence's open-source packages (MIT) are pinned to the versions of the last community template (2026-02-06: `@evidence-dev/evidence` 40.1.8). Evidence's newer "Evidence Studio" CLI needs an Evidence account and a hosted data connection, so it is not used here. The community template has been deprecated in favour of that product (2026-08-20), so treat this as a snapshot: the repository is active and MIT-licensed, but the project's long-term support for the community packages is not something this prototype relies on.

## Known risks (checked 2026-10-29)
- `npm audit` reports 34 findings (4 critical, 11 high), all in Evidence's own build and dev tooling (Vite dev server, Vitest, SvelteKit, regex DoS in `minimatch` and `trim`), none in the generated static site. They matter if the dev server is reachable from a network or fed untrusted input. This project only feeds it its own CSVs. Do not run `npm audit fix --force` (it changes major versions and can break the build); upgrade deliberately when Evidence publishes a release.
- Four install scripts (`@sveltejs/kit`, `esbuild`, `svelte-preprocess`) were not auto-approved by npm 11; the build ran without them.
- Before this goes into CI or Pages: review the dependency tree, decide who updates it, and add the build to the Pages workflow as a separate step.

## Limits of the page
The trend has one point per refresh, so the lines are short. Sport counts include sports inferred as also played on tennis courts (the map labels those inferred); the page says so.
