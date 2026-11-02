# Court usage: what we can measure for free (2026-11-02)

Question: how many people use which courts, how often, what kinds of people, and can it feed prediction? Constraint: little to no money, no accounts, no personal data (ADR 0013).

**The map can only see looks, not play.** So: measure demand in the app, ask for actual use from opt-in reports, and look for public data. Nothing here is shown as confirmed use.

## 1. Demand counts (BUILT, GoatCounter, free)
On every venue open the app now also sends three rows (`trackDemand` in `app/index.html`; fixed vocabularies, never a venue name, search text or coordinates):
- `event/demand-when/<weekday>-<am|pm|eve>` on the visitor's own clock.
- `event/demand-where/<city> <state>` of the venue opened.
- `event/demand-sport-where/<sport> <city>` when a sport filter was on.

Read them with `make usage`. Cost: 3 extra events per venue open, so watch the free-tier hit count in the first week and drop `demand-where` first if it is close. Not shown in the app; analytics is off on localhost, so check it on the live site.

## 2. "How busy is it?" report (NOT built, ask in the beta first: question 14)
One anonymous tap on a venue popup: sport, empty / some / full, time bucket. Goes to a Google Form -> Sheet like the suggest-a-change form (`docs/community_reports_plan.md`). No accounts, no individual rows published, only aggregates, labelled "reported by visitors". Optional coarse "who" (age band, level in the sport's own scale) only as the person states it, shared with `docs/player_finding_plan.md`. Cold start is the risk: seed it with beta testers and judge by question 14.

## 3. Public data (CHECKED 2026-11-02, thin)
A standard web search found no open reservation, permit or attendance dataset for CA or NV cities. San Francisco publishes reservation rules and a quarterly park-info dataset, not bookings; its tennis and pickleball reservation use was only reported in a 2019 write-up; Los Angeles has a facilities dataset (2020) and no usage file; nothing found for Las Vegas or Reno. Washington DC publishes recreation-center attendance (CC BY 4.0) and Seattle a pickleball court inventory: neither is in scope until ADR 0028 (five states) lands. Next, only if wanted: a public-records request for one city's reservation counts. Do not scrape booking apps (ADR 0007) or use Google "popular times" (ADR 0005).

## 4. Prediction: what is realistic
- Now: demand vs coverage (which sport and city needs courts next): demand counts + `make usage` + `make interest` (Google Trends). Planning signal, not a forecast.
- Later, only after weeks of busy reports per venue: hour-of-week average plus weather (Open-Meteo, free). Nothing per venue is predictable at beta traffic.
