# Usage analysis with GoatCounter

How to turn the anonymous counts (ADR 0013) into decisions. Counts are directional: ad blockers and Do Not Track hide some visits, there are no per-visitor funnels, and your own visits count until you exclude them (per browser and device: add `#toggle-goatcounter` to the live URL once, see `docs/feedback_round.md`; or GoatCounter -> Settings -> Ignore IPs).

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
| `event/demand-when/<weekday>-<am\|pm\|eve>`, `event/demand-where/<city> <state>`, `event/demand-sport-where/<sport> <city>` | looks at a venue by visitor weekday and part of day, venue city, and active sport filter (interest, not play; `docs/court_usage_plan.md`) |
| `event/ask-open`, `event/ask-kind/<reply kind>`, `event/ask-empty/<kind>`, `event/ask-sport/<sport>`, `event/ask-where/<city or area>` | the ask box (ADR 0033): opened, what kind of reply each question got (venues, events, clarify, refuse, ...), a search reply with no results, and the sport and place the question named. Sport and place are names from our own lists (`meta` in `app/ask.js`), never the typed text |
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
| Do people get answers from the ask box? | `ask-kind` refuse/clarify/offtopic share and `ask-empty` on the dashboard; a high share is the next rules to write |
| Does search demand match our coverage? | dashboard "Search interest against coverage": Google Trends interest per metro and sport (an outside signal, relative and sampled; the site's own events are sparse) next to venues and completeness; from `docs/search_interest_vs_coverage.csv` (`make interest`, `docs/search_interest_plan.md`) |
| Are the popular sports and cities also the accurate ones? | dashboard "Accuracy against popularity": picks, link-outs, asks and venue opens next to how complete each sport's and city's venues are |
| Which features can go? | habit events at zero after the beta are candidates to simplify |

## Check once
GoatCounter may keep one title per event path, which would merge the titles of `event/linkout` and `event/sport` (the original ADR 0013 events, where the detail was only in the title). The new `linkout-domain/*` and `sport-pick/*` rows do not depend on titles. After the first week of real traffic, open the dashboard: if `event/linkout` shows several titles, the title is kept per row and the old events can be retired in favour of the new ones.
