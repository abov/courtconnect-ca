# Usage analysis with GoatCounter

How to turn the anonymous counts (ADR 0013) into decisions. Counts are directional: ad blockers and Do Not Track hide some visits, there are no per-visitor funnels, and your own visits count until you exclude your IP (GoatCounter -> Settings -> Ignore IPs).

## Run it
1. One-off: GoatCounter -> Settings -> API -> create a token with "View statistics" only, put it in `.env` as `GOATCOUNTER_API_TOKEN`.
2. `make usage` (or `ARGS="--days 7" make usage`) exports daily counts to `goatcounter_daily.csv` in the shared raw folder and prints the report. Nothing is written to the repo.
3. For the beta, run it at the start and end of the round and paste the numbers into `docs/feedback_findings.md`.

## Events (all sent from `app/index.html`; the detail is in the path, so each value is its own row)
| Event path | Meaning |
|---|---|
| `event/venue-open`, `event/linkout`, `event/sport`, `event/suggest-change`, `event/osm-edit`, `event/report-form` | the ADR 0013 set; `linkout` stays one total path (the north star) |
| `event/linkout-domain/<domain>` | which provider got the click |
| `event/linkout-kind/<kind>` | website, tickets, event-page, signup, details, or `act-<type>` for a venue's join links |
| `event/linkout-sport/<sport>` | the sport filter that was active at the click (not the venue clicked) |
| `event/sport-pick/<sport>` | a sport was picked (same as `event/sport`, but one row per sport) |
| `event/empty-play/<sport>`, `event/empty-watch/<sport>` | a sport or filter pick left nothing on the map (`any sport` when none was picked) |
| `event/search-miss/<reason>` | a search found nothing: `no-match`, `zip-outside`, `place-no-venues`, `place-no-events` |
| `event/mode/<play or watch>`, `event/filter/<key>` | mode switches and filters turned on (surface, access, `offer-<code>`) |
| `event/ref/<source>` | the shared link that brought the visit (`?ref=`) |
| `share`, `shortlist-add/open/copy`, `focus-on`, `welcome-back`, `this-week-open`, `map-key` | habit events: is the feature used at all |

Never sent: search text, venue names, places, coordinates. Details are fixed vocabularies.

## Questions this answers
| Question | Where |
|---|---|
| Does the map deliver? | link-out rate = `linkout` / `venue-open`, target 25% (`docs/feedback_round.md`) |
| Which providers matter? | link-outs by domain: prioritise verifying those providers' pages |
| Which sports convert? | link-outs by sport filter vs sport picks |
| Where do people look but find nothing? | `empty-*` plus `search-miss/place-no-venues` vs `mart_sport_gaps`: the report's last table. A sport with many picks and empty or sparse coverage is the next facility scan |
| Is Watch / Social used? | `mode/watch` vs `mode/play`, `linkout-kind` event-page / tickets / signup |
| Which communities send people who stay? | `ref/*` visits vs the link-out total (ask: do shared posts convert?) |
| Which features can go? | habit events at zero after the beta are candidates to simplify |

## Check once
GoatCounter may keep one title per event path, which would merge the titles of `event/linkout` and `event/sport` (the original ADR 0013 events, where the detail was only in the title). The new `linkout-domain/*` and `sport-pick/*` rows do not depend on titles. After the first week of real traffic, open the dashboard: if `event/linkout` shows several titles, the title is kept per row and the old events can be retired in favour of the new ones.
