# RacketConnect project hub

The one place to find everything: live pages, dashboards, tools, and every doc in this folder. Start here; every other index points back here. `ci/check_docs_hub.py` fails CI if a doc in `docs/` is not listed below or a link here is broken, so this page cannot drift.

**To update:** add or rename a doc, then add or fix its one line in the right section below (same PR). Live-page and tool links are in the first three tables; change them here only.

## 1. Live pages (public)

| What | Link |
|---|---|
| Live map | <https://abov.github.io/courtconnect-ca/> |
| How it's built (numbers, gates, limits) | <https://abov.github.io/courtconnect-ca/how-its-built.html> |
| Ask the data (plain-English questions or SQL on the public venue file, in your browser) | <https://abov.github.io/courtconnect-ca/ask-the-data.html> |
| Database docs and lineage (dbt docs, built from sample data) | <https://abov.github.io/courtconnect-ca/dbt-docs/#!/overview> |
| Venue data dictionary and `llms.txt` (for builders and AI tools) | [`app/data-dictionary.md`](../app/data-dictionary.md), [`app/llms.txt`](../app/llms.txt) |

## 2. Source, tools and accounts

| What | Link | Access |
|---|---|---|
| Repository and README | <https://github.com/abov/courtconnect-ca> | public |
| Competitor differences | [`competitor_scan.md`](competitor_scan.md) | in repo |
| What it costs to run | [`running_costs.md`](running_costs.md) | in repo |
| Tools and strategies (one-page inventory) | [`tools_and_strategies.md`](tools_and_strategies.md) | in repo |
| Tool dictionary (every tool, lifecycle, license, glossary) | [Google Sheet](https://docs.google.com/spreadsheets/d/1RWONK-tLDJh5lRNyAISlNMEY4UH9ZHWGSW2ytlo5k1c/edit?gid=0#gid=0) | private (owner) |
| Scheduled cloud routines | <https://claude.ai/code/routines> | owner login; see [`cloud_routines.md`](cloud_routines.md) |
| Decision records (ADRs 0001-0039) | [`decisions/`](decisions) | in repo |

When a tool, library, service or data source is added or removed, update its row in the tool dictionary and [`tools_and_strategies.md`](tools_and_strategies.md) in the same task.

## Metrics and monitoring (every view, one table)

Each question has one home; other pages link here instead of repeating it.

| Question | Where | Refresh |
|---|---|---|
| Is the data complete and fresh? (counts, trends, coverage) | [Dashboard](https://abov.github.io/courtconnect-ca/dashboard/), [run history](https://abov.github.io/courtconnect-ca/run-history.html); [`data_quality.md`](data_quality.md), [`coverage_snapshot.md`](coverage_snapshot.md) | `make quality`, `make report`, each refresh |
| Is the pipeline healthy? (row-count anomalies, test history) | Elementary report, [`data_observability.md`](data_observability.md) | `make build`, `make observability` |
| Is the site up? | UptimeRobot monitors (owner email alerts), [`decisions/0037-uptime-monitoring.md`](decisions/0037-uptime-monitoring.md) | automatic |
| Who uses it? | [GoatCounter](https://courts.goatcounter.com/) (owner login), [`goat_analysis.md`](goat_analysis.md) | `make usage` |
| What is slowing delivery? (merged PRs per day, conflict commits, CI and build times, Claude token use) | [`ops_metrics.md`](ops_metrics.md) | `make ops-metrics` |
| What does it cost? | [`running_costs.md`](running_costs.md) | by hand |

## 3. Quick start for a new person
1. Read [`../README.md`](../README.md) (what it is, quick start, how to edit the data), then [`case_study.md`](case_study.md) (the story in one read).
2. Understand the build: [`architecture.md`](architecture.md), [`data_guide.md`](data_guide.md), the ADRs.
3. Change something: seeds under `transform/seeds/`, then `make build` and `make app-data` ([`data_guide.md`](data_guide.md); [`../CONTRIBUTING.md`](../CONTRIBUTING.md) for reports and PRs).
4. Reuse it elsewhere: [`fork_guide.md`](fork_guide.md). Add a state or country: [`new_region_checklist.md`](new_region_checklist.md).
5. What is being worked on: [`status.md`](status.md).

## 4. Every doc, by purpose

### Understand it
- [`case_study.md`](case_study.md): the problem, trade-offs and incidents.
- [`architecture.md`](architecture.md) (with `architecture.svg`): layers and flow.
- [`tools_and_strategies.md`](tools_and_strategies.md): tools, sources, governance, ML, CI.
- [`data_guide.md`](data_guide.md): sources, seeds and how to edit them.
- [`scale.md`](scale.md): what the extracts read of Overture, and how build time grows with data.
- [`running_costs.md`](running_costs.md): hosting, data, CI and the capped AI agents.
- [`talk_outline.md`](talk_outline.md), [`articles/`](articles): walkthrough outline and write-ups.

### Product, market and plans
- [`product_brief.md`](product_brief.md), [`value_proposition.md`](value_proposition.md): who it is for and why each piece exists.
- [`competitor_scan.md`](competitor_scan.md), [`market_insights.md`](market_insights.md), [`search_interest_plan.md`](search_interest_plan.md), [`sport_directories.md`](sport_directories.md): who else is out there and where demand is.
- [`monetization_ideas.md`](monetization_ideas.md), [`email_provider_comparison.md`](email_provider_comparison.md): after-beta ideas (ideas only).
- [`status.md`](status.md): priorities and dated detail. History: [`archive/session_digest.md`](archive/session_digest.md).
- Feature plans: [`player_finding_plan.md`](player_finding_plan.md), [`sport_discovery_plan.md`](sport_discovery_plan.md), [`sport_recommendation_plan.md`](sport_recommendation_plan.md), [`racket_vacations_plan.md`](racket_vacations_plan.md), [`court_usage_plan.md`](court_usage_plan.md), [`walls_into_venues_plan.md`](walls_into_venues_plan.md), [`community_reports_plan.md`](community_reports_plan.md), [`self_service_plan.md`](self_service_plan.md), [`recheck_queue_plan.md`](recheck_queue_plan.md).
- Ask box: [`chatbot.md`](chatbot.md) (plan, test questions, UX todo).
- Beta and UX: [`feedback.md`](feedback.md) (round plan and findings), [`ux_polish.md`](ux_polish.md).

### Data quality and monitoring
- [`data_quality.md`](data_quality.md): scorecard and SLAs. [`coverage_snapshot.md`](coverage_snapshot.md): generated by `make report`.
- [`data_observability.md`](data_observability.md): Elementary pipeline health. [`ops_metrics.md`](ops_metrics.md): delivery and workflow metrics. [`looker_studio.md`](looker_studio.md): second BI view.
- [`gold_set_plan.md`](gold_set_plan.md): the Overture/OSM match gold set. [`osm_fix_list.md`](osm_fix_list.md), [`contribute_to_osm.md`](contribute_to_osm.md): fixing OpenStreetMap.
- Usage: [`goat_analysis.md`](goat_analysis.md).

### Run it (runbooks)
- [`monthly_refresh.md`](monthly_refresh.md): the twice-monthly refresh.
- [`cloud_routines.md`](cloud_routines.md): the scheduled cloud routines and their ids.
- [`tournament_run_parts.md`](tournament_run_parts.md) (the five parts), [`tournament_refresh.md`](tournament_refresh.md) (tournament steps), [`tournament_sources.md`](tournament_sources.md) (source list and the table tennis/badminton pass), [`event_group_search.md`](event_group_search.md) (events, leagues, groups per state).
- [`refresh_agent.md`](refresh_agent.md), [`merge_gate_threat_model.md`](merge_gate_threat_model.md): the agent and its merge gate (ADR 0019).
- [`new_region_checklist.md`](new_region_checklist.md), [`fork_guide.md`](fork_guide.md): new regions and forks.
- Session notes from the automated routines only: [`sessions/`](sessions).

### Research passes and scans (dated results)
- Venues: [`padel_scan.md`](padel_scan.md), [`public_facility_scan.md`](public_facility_scan.md), [`gym_chain_scan.md`](gym_chain_scan.md), [`hawaii_resorts.md`](hawaii_resorts.md), [`beach_tennis_watch.md`](beach_tennis_watch.md).
- Mexico: [`mexico_metro_trial.md`](mexico_metro_trial.md), [`mexico_apps_research.md`](mexico_apps_research.md), [`mexico_states_outline.md`](mexico_states_outline.md).
- Names: [`sport_name_review.md`](sport_name_review.md).

### ML and AI
- [`ml.md`](ml.md): strategy, plan and discovery in one file.

### Data files kept here
CSV and JSON files in `docs/` are outputs of scripts (`agent_log.csv`, `data_quality_trend.csv`, `feedback_log.csv`, `usage_*.csv`, `ml_metrics.csv`, `planet_scale_benchmark.json`, scan results and more); the dashboard reads several of them. Do not hand-edit. Screenshots are in `screenshots/`, gym scan results in `gym_scans/`.
