# Tools and strategies

One-page inventory. All links and docs: [`README.md`](README.md) (project hub). Layout and layers: [`architecture.md`](architecture.md). Decisions: [`decisions/`](decisions).

The long version is the owner's Google Sheet [RacketConnect tool dictionary](https://docs.google.com/spreadsheets/d/1RWONK-tLDJh5lRNyAISlNMEY4UH9ZHWGSW2ytlo5k1c/edit) (private; every tool with what it is, how it is used here and elsewhere, lifecycle stage and license, plus a lifecycle tab and a glossary). Whenever a tool, library, service or data source is added or removed, update the sheet (a row on the Dictionary tab, and the Lifecycle tab if a step changes) and this page in the same change.

## Languages and runtime
- Python 3.12 (ingestion, export, checks, ML), SQL (dbt), JavaScript/HTML/CSS (map), Bash and `make` as the task runner.
- `.venv`; `requirements-ml.txt` for the optional ML dependencies.

## Data sources (public and open only)
- OpenStreetMap via Overpass (courts, walls, parent parks and schools), Overture Maps places and addresses (S3), US Census place and county boundaries (Mexico: Overture divisions municipios and localities, ADR 0034), Nominatim reverse geocoding (cached), the Google Sheet sports list, public venue and city pages, community reports and GitHub issues.
- Not used: Google Places (ADR 0005), owner logins (ADR 0007), directory sites whose terms forbid reuse.

## Back end
- Python extract/load scripts in `ingestion/`; one shared raw-CSV folder across worktrees (`rawdir.py`); `load_raw.py` shrink guard.
- DuckDB as the only warehouse (ADR 0018); `fresh_db.py` rebuilds a worktree database in about a minute.

## Transformation (dbt)
- dbt-core + dbt-duckdb; staging, intermediate, core (star schema) and marts; about 28 CSV seeds as the knowledge layer; `adapter.dispatch` macros kept.
- Proximity clustering of courts into venues, Overture-to-OSM place matching, rules-based confidence score (`rules_v2`), sport-fit reference table.
- dbt tests and dbt docs (lineage and data dictionary); dbt model contracts enforced on the five marts the app export reads (`transform/models/schema.yml`).

## Data quality and governance
- Evidence required on every seed fact (`evidence` + `verified_on`); confirmation levels; `inferred` labels and provenance fields (`address_source`, `address_distance_m`).
- Privacy: homes show the city only, no personal contact in outbound requests, phone numbers never exported.
- Quality scorecard with a 35-day freshness SLA and a no-regression check; link and website checkers; coverage reports; hand-labelled gold set for the match (`make eval-match`).
- ADRs as the decision record.

## ML and AI
- scikit-learn review-queue ranker (suggests only; never feeds dbt or the map).
- Gold-set evaluation of the entity-resolution rules, enforced in CI.
- Address fill by deterministic tiers (OSM tags, nearest Overture point, Nominatim, official page).
- LLM page reader (ADR 0017): fixed fields, exact-quote check in code, staged candidates, human approval, spend cap.
- NAIP aerial-imagery pilot (lead generator for OSM); imagery checks for padel court size.

## CI/CD
- GitHub Actions: `ci.yml` (fixture data, gate scripts, `dbt build`), `issue-to-pr.yml`, `pages.yml`.
- Uptime check (live since 2026-11-11, ADR 0037): UptimeRobot free, two monitors on the live page and `data/venues.json`, email alert to the owner; nothing in the repo or the page. Pipeline health stays with Elementary (`docs/data_observability.md`). Delivery speed, conflict commits and Claude token use: `make ops-metrics` (`docs/ops_metrics.md`; `gh` CLI plus local session logs, nothing sent anywhere).
- Squash-merge after green checks; `venues.json` regenerated, never hand-merged.

## Front end
- Static MapLibre page (`app/index.html`) over one `venues.json`; Play / Watch / Social modes; filters in the URL; link-outs; suggest-a-change form; GoatCounter analytics (ADR 0013); GitHub Pages hosting.

## Workflow and agentic strategies
- Twice-monthly runbook; git worktrees per session; one task per session with hand-off in the PR description (`docs/sessions/` is only for the automated routines); `CLAUDE.md` and memory files as persistent guidance.
- Cost control: cheapest path first, narrowest check first, no scheduled tasks or extracts unasked.
- Observe, propose, verify, merge loop; automated gates in place of pre-approval; staged autonomy (ADR 0019): agents open PRs, humans merge, a class auto-merges only after it earns it and the owner switches it on; kill switch and spend cap ($20/month) ([`self_service_plan.md`](self_service_plan.md)).
- Honesty over polish: label inferred data, never present guesses as confirmed.
