# What it costs to run CourtConnect

*Written 2026-10-29. Every number comes from a repo doc, a file in the repo or a GitHub query run that day; where I did not check something, it says so. Short version: the recurring bill I can point to is zero, and the only spend that is capped is the AI agents.*

## Where the money would go, and what I found

| Item | What the repo says | Cost shown |
|---|---|---|
| **Hosting** | Static site on GitHub Pages ([architecture](architecture.md)). `app/` is about 2.9 MB, 2.45 MB of it the one data file; the dbt docs are added at deploy and I did not measure them. GitHub publishes limits of 1 GB per site and 100 GB a month of bandwidth (soft). | $0 on the project's side. I did not find GitHub stating Pages is free for public repos, so that rests on the repo being public. |
| **CI and deploys** | Public repository. GitHub's billing page says standard hosted runners are free in public repositories. In the 40 most recent `ci` runs, 32 succeeded: median 50 s, 26.5 min in total. Of the 40 most recent `pages` runs, 37 succeeded: median 74 s, 48.3 min in total. | $0. All of that fell on one busy day (2026-10-29); I did not read the account's billing page. |
| **Data sources** | OpenStreetMap, Overture, US Census boundaries, Nominatim (1 request a second, results cached) and NAIP imagery are public and need no key. The Overture extract fetches about 743 MB of 39.6 GB ([benchmark](planet_scale_benchmark.md)). | $0 in fees. The cost is the owner's bandwidth and about 15 minutes per extract. |
| **Warehouse** | DuckDB in a file on the owner's machine, no server ([ADR 0018](decisions/0018-duckdb-only.md)). A fresh database builds in about a minute (`CLAUDE.md`). | $0. Snowflake was retired on 2026-10-14. |
| **Analytics** | GoatCounter, "free for non-commercial use" ([ADR 0013](decisions/0013-usage-analytics.md)). | $0 today. **It stops being free if the project is monetized** ([ideas](monetization_ideas.md)): that is my reading of "non-commercial", not a checked licence. |
| **One-off ML** | The aerial pilot's first run (Hawthorne) trained for about 80 minutes on a CPU and fetched about 25 MB of imagery ([ML plan](ml_plan.md)). | $0 in fees; stopped on purpose. |
| **AI agents** | The only capped spend: **$20 a month and $5 a week** project-wide ([ADR 0019](decisions/0019-unattended-agent-merges.md)); the refresh agent's own cap is $5 a week and $10 a month ([refresh agent](refresh_agent.md)). The agent logs about $1.50 per run, and [`agent_log.csv`](agent_log.csv) holds 2 runs, about $3.00 estimated. | Estimates only. At the planned two refreshes a month that is about $3 a month, under both caps. |

## How spend is held down

- **Free first, paid optional.** The page reader runs a free rules engine today. The Claude engine waits on an API key, a spend cap and a precision bar ([ADR 0017](decisions/0017-llm-page-reader.md)).
- **Caps before runs.** The agent checks the last 7 and 30 days of logged cost before it starts and aborts if this run would pass either cap. `AGENTS_ENABLED` is a kill switch that fails closed.
- **Pay once per page.** The reader caches each page's text and result by URL and date, sends page text only, and a dry run prints the token estimate first.
- **Nothing to leave running.** There is no server, database or queue to pay for between refreshes.

## What this does not show

- **The agent cost figures are estimates, not invoices.** I have no billing data for them, and the repo does not say whether agent runs are billed per call or sit inside a subscription.
- **Owner time is the real cost and I have not measured it.** Review time per refresh is not logged. The goal of driving it toward zero is stated in [ADR 0015](decisions/0015-mission-and-social-phase.md); a target (for example under an hour a month) is only suggested in [`ml_strategy.md`](ml_strategy.md).
- **It is small-scale.** About 10,000 venues, twice-monthly refreshes and no accounts. Nothing here says what an always-on service, accounts, email alerts or a hosted backend would cost; ADR 0025 and 0024 put those out of the current budget.
- **Free tiers can change.** The limits above were read on 2026-10-29.
