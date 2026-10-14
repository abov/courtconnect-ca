# 0013. Anonymous usage analytics (GoatCounter)

Date: 2026-10-13. Status: accepted (2026-10-13); live since 2026-10-13 (GoatCounter site code `courts`).

## Context
We need real usage numbers (for deciding what to build, for the feedback round, and for the case study) without tracking people.

## Decision
- Use GoatCounter (free for non-commercial use, no cookies, no personal data stored, can be self-hosted later). One script from `gc.zgo.at`.
- Disabled by default: `GOATCOUNTER_CODE` in `app/index.html` is empty. It is also off on localhost and when the browser sends Do Not Track.
- Counts page views plus five named events, never anything a visitor typed or a place they looked at:

| Event path | Meaning |
|---|---|
| `event/venue-open` | a venue panel was opened |
| `event/linkout` (title = domain, e.g. `southendclub.com`) | an outbound link was clicked (website, join, tickets); the domain tells us which providers matter |
| `event/suggest-change` | the "Suggest a change" link was clicked |
| `event/osm-edit` | the "Fix on OpenStreetMap" link was clicked |
| `event/sport` (title = sport name) | a sport was picked in the dropdown (sport names are public, not personal) |

- When on, the page footer says so.
- A failing or blocked analytics script must never break the map (all calls are wrapped).

## Metrics (defined here so the numbers mean the same thing every time)
- **North star:** outbound link-outs per week (`event/linkout`). A link-out is the moment the map did its job (the player went to the provider).
- **Engagement:** venue opens per visit = `venue-open` / page views.
- **Usefulness:** link-out rate = `linkout` / `venue-open`.
- **Contribution:** `suggest-change` + `osm-edit` per week.
- **Demand by sport:** `sport` events, to compare with coverage in `docs/data_quality.md` (where people look vs what we have).

## Owner setup (once)
1. Create a free account at goatcounter.com and a site; pick a code (the part before `.goatcounter.com`).
2. Set `GOATCOUNTER_CODE` in `app/index.html`, merge, and re-run `pages.yml`.
3. Events are sent from the page, so no extra GoatCounter setting is needed. Keep the dashboard private, or make it public if you want to link it from the case study.

## Consequences
Cheap and private, but counts are approximate: ad blockers and Do Not Track hide some visits, and there are no user-level funnels. That is the point.
