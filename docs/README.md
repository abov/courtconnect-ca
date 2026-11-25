# RacketConnect project hub

One free map of every racket sport, from park courts to private clubs. Pick the door that fits you.

**To update:** this page stays short on purpose. Add or rename a doc, fix its one line under All docs and tools, then run `make hub`; CI fails if a doc is unlisted, a link is broken or the web page is stale.

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

- [All docs and tools](#all-docs-and-tools), below: every runbook, monitor, plan and research note.
- [Project README](../README.md): quick start and how to edit the data. Then the [twice-monthly refresh](monthly_refresh.md).
- [Status](status.md): what is being worked on now.

## All docs and tools

Every doc, runbook, monitor and tool, grouped by purpose, with a search box. Docs open on GitHub; each question has one home here, other pages link instead of repeating it.

### Live pages

[Map](https://abov.github.io/courtconnect-ca/), [project hub](https://abov.github.io/courtconnect-ca/hub.html), [how it's built](https://abov.github.io/courtconnect-ca/how-its-built.html), [ask the data](https://abov.github.io/courtconnect-ca/ask-the-data.html), [run history](https://abov.github.io/courtconnect-ca/run-history.html), [database docs and lineage](https://abov.github.io/courtconnect-ca/dbt-docs/#!/overview) (dbt docs, built from sample data), and for builders and AI tools the [data dictionary](../app/data-dictionary.md) and [`llms.txt`](../app/llms.txt).

### Understand it
- [Source repository](https://github.com/abov/courtconnect-ca) and [`../README.md`](../README.md): what it is, quick start, how to edit the data. Reports and PRs: [`../CONTRIBUTING.md`](../CONTRIBUTING.md).
- [`case_study.md`](case_study.md): the problem, trade-offs and incidents.
- [Decision records](decisions) (ADRs 0001-0041).
- [`architecture.md`](architecture.md) (with `architecture.svg`): layers and flow.
- [`tools_and_strategies.md`](tools_and_strategies.md): tools, sources, governance, ML, CI. The tool dictionary (every tool, lifecycle, license) is a private [Google Sheet](https://docs.google.com/spreadsheets/d/1RWONK-tLDJh5lRNyAISlNMEY4UH9ZHWGSW2ytlo5k1c/edit?gid=0#gid=0) (owner); update its row and this file's in the same task whenever a tool, library, service or data source is added or removed.
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
- Live: the [dashboard](https://abov.github.io/courtconnect-ca/dashboard/) and [run history](https://abov.github.io/courtconnect-ca/run-history.html). Site up? UptimeRobot monitors (owner email alerts), [`decisions/0037-uptime-monitoring.md`](decisions/0037-uptime-monitoring.md).
- [`data_quality.md`](data_quality.md): scorecard and SLAs. [`coverage_snapshot.md`](coverage_snapshot.md): generated by `make report`.
- [`data_observability.md`](data_observability.md): Elementary pipeline health. [`ops_metrics.md`](ops_metrics.md): delivery and workflow metrics. [`agent_activity.md`](agent_activity.md): live agent activity page. [`looker_studio.md`](looker_studio.md): second BI view.
- [`gold_set_plan.md`](gold_set_plan.md): the Overture/OSM match gold set. [`osm_fix_list.md`](osm_fix_list.md), [`contribute_to_osm.md`](contribute_to_osm.md): fixing OpenStreetMap.
- Usage: [GoatCounter](https://courts.goatcounter.com/) (owner login), [`goat_analysis.md`](goat_analysis.md).

### Run it (runbooks)
- [`monthly_refresh.md`](monthly_refresh.md): the twice-monthly refresh.
- [`merge_conflicts.md`](merge_conflicts.md): how the repo avoids PR merge conflicts (venues.json layout and merge driver, union merges, rerere).
- [`working_practices.md`](working_practices.md), [`commands.md`](commands.md), [`token_efficiency.md`](token_efficiency.md): build and ship practices, every `make` target, and the hooks that keep sessions cheap (moved out of `CLAUDE.md`).
- [`cloud_routines.md`](cloud_routines.md): the scheduled cloud routines and their ids; run at <https://claude.ai/code/routines> (owner login).
- [`tournament_run_parts.md`](tournament_run_parts.md) (the five parts), [`tournament_refresh.md`](tournament_refresh.md) (tournament steps), [`tournament_sources.md`](tournament_sources.md) (source list and the table tennis/badminton pass), [`event_group_search.md`](event_group_search.md) (events, leagues, groups per state).
- [`refresh_agent.md`](refresh_agent.md), [`merge_gate_threat_model.md`](merge_gate_threat_model.md): the agent and its merge gate (ADR 0019). The weekly audit digest and the Dependabot config are described in the threat model and [`SECURITY.md`](https://github.com/abov/courtconnect-ca/blob/main/SECURITY.md) (reporting a vulnerability, scope, what is in place).
- [`new_region_checklist.md`](new_region_checklist.md), [`fork_guide.md`](fork_guide.md): new regions and forks.
- Session notes from the automated routines only: [`sessions/`](sessions).

### Research passes and scans (dated results)
- Venues: [`padel_scan.md`](padel_scan.md), [`website_finder.md`](website_finder.md) (official websites for pins with none: script first, model for the rest), [`public_facility_scan.md`](public_facility_scan.md), [`gym_chain_scan.md`](gym_chain_scan.md), [`hawaii_resorts.md`](hawaii_resorts.md), [`beach_tennis_watch.md`](beach_tennis_watch.md).
- Mexico: [`mexico_metro_trial.md`](mexico_metro_trial.md), [`mexico_apps_research.md`](mexico_apps_research.md), [`mexico_states_outline.md`](mexico_states_outline.md).
- Names: [`sport_name_review.md`](sport_name_review.md).

### ML and AI
- [`ml.md`](ml.md): strategy, plan and discovery in one file.

### Data files kept here
CSV and JSON files in `docs/` are outputs of scripts (`agent_log.csv`, `data_quality_trend.csv`, `feedback_log.csv`, `usage_*.csv`, `ml_metrics.csv`, `planet_scale_benchmark.json`, scan results and more); the dashboard reads several of them. Do not hand-edit. Screenshots are in `screenshots/`, gym scan results in `gym_scans/`.
