# Tools and strategies

One-page inventory. Layout and layers: [`architecture.md`](architecture.md). Decisions: [`decisions/`](decisions).

## Languages and runtime
- Python 3.12 (ingestion, export, checks, ML), SQL (dbt), JavaScript/HTML/CSS (map), Bash and `make` as the task runner.
- `.venv`; `requirements-ml.txt` for the optional ML dependencies.

## Data sources (public and open only)
- OpenStreetMap via Overpass (courts, walls, parent parks and schools), Overture Maps places and addresses (S3), US Census place and county boundaries, Nominatim reverse geocoding (cached), the Google Sheet sports list, public venue and city pages, community reports and GitHub issues.
- Not used: Google Places (ADR 0005), owner logins (ADR 0007), directory sites whose terms forbid reuse.

## Back end
- Python extract/load scripts in `ingestion/`; one shared raw-CSV folder across worktrees (`rawdir.py`); `load_raw.py` shrink guard.
- DuckDB as the only warehouse (ADR 0018); `fresh_db.py` rebuilds a worktree database in about a minute.

## Transformation (dbt)
- dbt-core + dbt-duckdb; staging, intermediate, core (star schema) and marts; about 28 CSV seeds as the knowledge layer; `adapter.dispatch` macros kept.
- Proximity clustering of courts into venues, Overture-to-OSM place matching, rules-based confidence score (`rules_v2`), sport-fit reference table.
- dbt tests and dbt docs (lineage and data dictionary).

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
- Squash-merge after green checks; `venues.json` regenerated, never hand-merged.

## Front end
- Static MapLibre page (`app/index.html`) over one `venues.json`; Play / Watch / Social modes; filters in the URL; link-outs; suggest-a-change form; GoatCounter analytics (ADR 0013); GitHub Pages hosting.

## Workflow and agentic strategies
- Twice-monthly runbook; git worktrees per session; one task per session with a note in `docs/sessions/`; `CLAUDE.md` and memory files as persistent guidance.
- Cost control: cheapest path first, narrowest check first, no scheduled tasks or extracts unasked.
- Observe, propose, verify, merge loop; automated gates in place of pre-approval; staged autonomy (ADR 0019): agents open PRs, humans merge, a class auto-merges only after it earns it and the owner switches it on; kill switch and spend cap ($20/month) ([`self_service_plan.md`](self_service_plan.md)).
- Honesty over polish: label inferred data, never present guesses as confirmed.
