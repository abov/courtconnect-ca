# 0037. Uptime check for the live site (UptimeRobot, free)

Date: 2026-11-11. Status: proposed (owner asked in chat 2026-11-11; the monitors are not created until the owner signs up and says go). Complements ADR 0013 (GoatCounter) and `docs/data_observability.md` (Elementary).

## Context
Nothing tells us the live map is down or serving a broken file. GoatCounter counts visits (a dead site just shows zeros), Elementary watches the local warehouse, CI runs only on merges. A full APM tool (Datadog, New Relic) was considered and rejected: RacketConnect has no server to instrument (static GitHub Pages plus a local batch pipeline), and those tools add an agent, an account and a secret for almost no signal.

## Decision
1. Use UptimeRobot's free plan: HTTP(S) checks every 5 minutes, email alert to the owner. Nothing is installed in the repo or the page; no script is added to the app, no visitor data is involved (the checks come from UptimeRobot to the public URL).
2. Two monitors:
   - `https://abov.github.io/courtconnect-ca/` with keyword `RacketConnect` (the page `<title>`): catches a failed Pages deploy or an empty page.
   - `https://abov.github.io/courtconnect-ca/data/venues.json` with keyword `"venues"` or the file's first stable key (confirm against the live file when creating it): catches a missing or truncated export, which is the map's only data source.
3. Alert goes to the owner only. No status page, no Slack/webhook, no paid tier.
4. Sentry (browser JS errors) is not part of this decision: it adds a third-party script to the page, so it needs its own ADR near the December beta.

## Consequences
- Free, about 5 minutes of owner setup (account + two monitors), zero code. Record the two monitors in the tool dictionary and `docs/tools_and_strategies.md` when created.
- Limits: 5-minute granularity, tells us the site is up, not that the map renders or the data is right (the quality scorecard and CI cover data). The free plan is for non-commercial use: revisit if the project is monetized (`docs/monetization_ideas.md`). Alternative if that bites: Better Stack free (3-minute checks).
- Agents cannot sign up for the account (accounts are the owner's to create); the owner shares nothing with the repo, since the alert goes to their own email.
