# CourtConnect CalNeva: case study

A free map of racket-sport venues in California and Nevada (tennis, pickleball, padel, squash, badminton, beach tennis and dozens more), built end to end as a solo project: ingestion, a tested dbt warehouse, a static map, and a gated, agent-assisted refresh process. Live map: https://abov.github.io/courtconnect-ca/. Code: https://github.com/abov/courtconnect-ca. Data model and lineage: `/dbt-docs/` on the Pages site.

**In one line:** the hard part was never the map. It was joining sources that disagree, saying honestly how far to trust each fact, and keeping the data current with as little human review as safe.

## At a glance
- **10,288 venues** from three source families, 41 of 82 sports with at least one venue, 7 of 8 service levels met (scorecard `make quality`, 2026-10-29).
- **53 dbt models, 34 seeds, 32 custom SQL tests**, plus column tests; **26 decision records**; 11 CI gate scripts.
- **Entity resolution measured on a gold set:** 129 labelled pairs, 0 wrong merges, 4 missed.
- **Reads about 2% of a 40 GB columnar source** to keep a few thousand venues (743 MB fetched of 39.6 GB, places and addresses themes).
- **No server, no database service, $0 hosting:** one 2.4 MB JSON export on GitHub Pages.

## The problem
Players of smaller racket sports cannot answer "where can I play this near me, and can I walk on?" Each sport has scattered, incomplete sources, and big map platforms treat a tennis court and a padel court as the same pin. Sources also disagree: OpenStreetMap has courts but few names, business directories have names but not courts, and clubs publish access rules only on their own pages.

## Users and constraints
- **Users:** me and friends who play several sports; later, possibly the wider community (open source or paid, not decided).
- **Constraints I set on purpose:** link out only (no bookings or payments); public pages only, never my own logins (ADR 0007); no Google Places data, whose terms forbid storing it (ADR 0005); inferred data is always labelled inferred; no accounts, cookies or personal data.

## Architecture
Raw sources land untouched, dbt cleans, matches and tests them, and one export feeds a static page. Diagram and layer table: [`architecture.md`](architecture.md).

| Layer | What | Why it matters |
|---|---|---|
| Ingestion | Python extract and load: OSM courts, parks and walls, Overture places and addresses (queried in place on S3), Census boundaries | Idempotent loads; the loader refuses to shrink a table by more than 10% |
| Warehouse | dbt on DuckDB: staging, intermediate (proximity graph, clustering, matching), core dimensions, marts | Human knowledge lives in seeds with `evidence` + `verified_on`, so facts are code-reviewed |
| Serving | Static MapLibre page fed by one JSON export, GitHub Pages | CI fails if the export is stale |
| Operations | Twice-monthly runbook, scheduled agent runs, issue-to-PR workflow, evidence checker | Data stays current without me guessing what changed |
| Governance | 26 ADRs, a confirmation scale (visited / official / reported / inferred) | Every claim says how we know it |

## Decisions and trade-offs
1. **Cluster courts into venues by proximity (ADR 0003).** OSM stores individual courts; users want places. Trade-off: some wrong merges and splits, so a convergence test, a duplicate guard and a gold set exist.
2. **Honesty over polish (ADR 0007).** Access is often inferred from a club's website, not stated. The map labels it inferred and the contributor workflow demands evidence and a date. A smaller, trustworthy dataset beat a bigger, guessed one.
3. **What I chose not to do (ADRs 0005, 0009, 0010, 0012).** No Google Places, no scraping of Meta, WhatsApp or Meetup, no use of my logins. Social groups are link-outs from a club's own page. This cut off easy data but removed legal and privacy risk.
4. **Portability, then retirement (ADR 0001, then 0018).** I first kept every model runnable on DuckDB and Snowflake. When Snowflake access went away (2026-10-14) nothing had run on it, so I recorded the decision, relaxed the portability rule and removed the dead code (PR #304) instead of maintaining an engine nobody tested. Lesson: a portability rule has a running cost, so drop it when its reason disappears.
5. **Query big data in place, keep small data.** DuckDB reads the Overture parquet on S3 with range requests and keeps only the CA+NV rows. Measured: [planet-scale benchmark](planet_scale_benchmark.md). It is not terabyte processing, and the doc says so.
6. **Give back to the source (ADR 0011).** OSM is the main input, so the map links venues to the OSM editor with a contributor guide, and a fix list (`osm_fix_list.md`) goes to people who edit OSM; we never edit it ourselves.
7. **Models suggest, code and people decide (ADR 0017, 0019).** See the next section.

## Analytics and BI
- **Scorecard with stated service levels** (`docs/data_quality.md`): freshness, dead links, name quality, with a dated trend. One level is breached and reported: only 16.2% of venues have a real name (goal 25%), because most OSM courts are unnamed. The breach is the top backlog item, not hidden.
- **Usage metrics** from cookie-free GoatCounter (ADR 0013), joined to coverage to compare sport demand with supply.
- **Planning signals:** Google Trends interest vs venues per metro, and market-insight marts (which sports are missing near a city). Labelled inferred and not shown in the app.
- **A public change feed** (`app/data/changes.json`) so subscribers could be told about new venues, closures and access changes.

## ML and agents: small models suggest, gates decide
- **Review-queue ranker:** logistic regression on 90 human labels, leave-one-out accuracy 86%, AUC 0.93. It only orders work for a reviewer. Checking what it learned, not just its score, showed skewed labels had taught it "Tennis means reject".
- **LLM page reader:** every extracted field needs an exact quote that code verifies is on the page (ADR 0017). Built; not run at scale until a spend cap and precision bar are agreed.
- **Aerial-imagery pilot:** measured (LV recall 46%), rescans found 0 new venues, so I dropped it. Killing a pilot on numbers is a result too.
- **Agent governance (ADR 0019):** a model never merges; a deterministic gate script decides, using risk classes, path allowlists, diff caps, scorecard no-regression and evidence rules. Today agents open PRs and people merge; routine refresh PRs can auto-merge only after the owner switches that on, and risky classes always escalate.

## How quality is measured and kept
- **Tests:** dbt singular tests guard the logic (clusters converge, every court has one venue, confirmed venues need evidence, no duplicate names within 150 m); CI runs on a small committed fixture and never calls a live source.
- **Gold set:** `make eval-match` scores the place-to-court matcher; it drove a name rule, a 300 m same-name radius and a footprint tier, each judged by score and not by eye.
- **Runbook:** a written, repeatable refresh procedure with gates at the end.

## Incidents worth learning from
- **Stale export (PR #7).** Seeds changed but `venues.json` was not re-exported, so the live site silently missed new sports and 43 events. Fix: re-export (#8) and a CI check that fails when the export is stale (#9). Lesson: a derived artifact needs an automated freshness guard, not a reminder.
- **Duplicates inflated the count.** Merging courts in one park and places at one address cut venues by about 3%; a guard test now fails if two venues share a name within 150 m.
- **Refreshing data does not fix a data gap; a different source does.** Pickleball hides on tennis courts and racquetball in gyms; park pages, chain scans and reports found them.

## Results and what is not measured yet
- Coverage and service levels: see "At a glance". Live numbers regenerate with `make quality` and `make report`.
- **Usage and friend feedback are not in yet:** a beta round is planned for December (`docs/feedback_round.md`). I will add weekly visitors, venue opens and link-out clicks then, and will not quote numbers before they exist.

## What I would do next
1. Run the beta and rank findings with RICE (`docs/feedback_findings.md`).
2. Raise name quality with a contributor drive and the OSM link.
3. Publish a lineage page and a small BI dashboard of the scorecard (static, fits Pages).
4. Decide the path: community open source (ODbL attribution already required) or a paid layer; the link-out-only rule keeps both open.

## Skills this shows
- **Data (large and small):** in-place columnar queries, idempotent loads, entity resolution with a measured gold set.
- **Analytics and BI:** service-level scorecards, demand vs supply, search-interest planning signals.
- **Development:** Python ingestion, dbt/SQL modelling and tests, a static MapLibre front end with no backend.
- **Architecture:** 26 written decisions, including reversing one.
- **Operations:** CI gates, freshness SLAs, runbooks, scheduled agent runs with a deterministic merge gate, privacy and licence limits.
