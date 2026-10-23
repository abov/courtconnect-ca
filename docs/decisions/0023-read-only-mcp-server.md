# 0023. An optional read-only MCP server over `venues.json`

Date: 2026-10-23. Status: **proposed**. Recommendation: **no-go on a hosted server; go on a small local one only after the beta shows demand**, and ship a cheaper static alternative first (see Alternatives, option 2). Nothing here is built or scheduled.

## Context
CLAUDE.md lists "Optional read-only MCP server over `venues.json` (was 8; ADR first)" under After beta. The mission (ADR 0015) is one map for every racket sport in CA + NV. Today the only way to use the data is the web page. More people now ask an AI assistant "where can I play padel near Reno?"; those assistants can only answer from our data if it is reachable in a form they can query.

`app/data/venues.json` is already public (served by GitHub Pages, 2.4 MB, 10,267 venues, 81 sports, plus events, social groups and walls; keys are single letters, so a raw dump is hard for a model to read). A server over it adds a friendlier door, not new data. That bounds the privacy risk, and also the value: it is only worth doing if assistants and people actually use it.

## Decision (if built)

### 1. Purpose
Let an AI assistant answer "where can I play X near Y", "what events are on", "is this a confirmed court" from our data, and always send the user on to the venue's own page. Same stance as the map: it links out, takes no bookings or payments.

### 2. Tools (all read-only, no write tools, no network calls from the server)
| Tool | Does |
|---|---|
| `list_sports` | The sheet's sport names, with venue counts and coverage status. |
| `search_venues` | `sport`, a place (city, zip or lat/lon), `radius_km` (default 25, max 100), `confirmed_only`, `limit` (default 10, max 25). Returns nearest first. |
| `get_venue` | One venue by id: name, city, sport(s) and court counts, access/rules text, link-outs, confidence and what is inferred. |
| `list_events` | Pro/amateur events and social series by sport, region and date range, each with its link. |
| `search_walls` | Hitting walls near a place (they are a separate export list). |

"Near Y" is resolved offline from `app/data/zips.json` and `places.json`. The server never calls a geocoder, so no request carries the owner's or a user's data to an outside service (CLAUDE.md rule).

### 3. What it must not expose
- **Personal contact:** no email, phone or owner name, in any field. The current export has none; the server uses an **allowlist of fields**, not a denylist, and a test fails the build if a result matches an email or phone pattern.
- **Private clubs and members-only places:** only what the map shows today: name, city, the "public access not confirmed" flag, link to the club's own page. No member rules beyond the map's text; no home-like pins' inferred streets (address privacy, ADR 0016). Nothing the export hides is reconstructed from other tables.
- **Google Places data:** none, and none can arrive: ADR 0005 keeps only Overture + OSM in the warehouse, and the export carries no Google fields. The place-ID layer stays dormant.
- **Raw tables, seeds, `.env`, evidence URLs behind unconfirmed reports,** and anything not in `venues.json`. Pickleheads/Places2Play-style data is off limits (existing memory rule).
- **Owner logins and logged-in pages** (ADR 0007): not involved; the server reads one public file.

### 4. Honesty in every answer
- Each result carries the map's labels as fields, not prose the model may drop: `quality` (named / inferred name / unnamed), `confirmation` (confirmed / reported / none, with date), `address_inferred`, `access_unconfirmed`, `source` (OSM, Overture, manual).
- Every response has `data_as_of` (the `meta.generated` date) and a one-line note: "Check the venue's own page before travelling; this data can be out of date." Inferred means inferred; the server never turns a guess into a "confirmed" in its own summary.
- Attribution travels with the data: OpenStreetMap contributors (ODbL), Overture (CDLA-Permissive / Apache / CC0), as in `meta.attribution`. A response that mixes records adds it once.
- Venue names, rules text and event titles come from third parties (OSM tags, web pages, reports). Return them as quoted data fields, length-capped and stripped of markup and URLs not in the `link` fields, so a hostile name cannot steer the calling assistant (same rule as ADR 0019, section 6).

### 5. Hosting, cost and freshness
| Option | Cost | Freshness | Verdict |
|---|---|---|---|
| **Local stdio** (a ~150-line Python or Node script the user runs from a clone or a release file; reads a local copy of `venues.json`) | $0 | As fresh as the user's copy; the script can fetch the Pages file on start if online and cache it. | Preferred if built. No hosting, no abuse surface, no uptime duty. |
| **Hosted remote** (free-tier serverless function, e.g. Cloudflare Workers, serving `venues.json` from Pages) | $0 until traffic; then a bill nobody budgeted | Always latest after a Pages deploy | Not now. Adds an endpoint to keep alive, secure and rate-limit for an unmeasured audience. |

Budget rule (project memory): free/open-source tools by default; any paid tier needs the owner's go-ahead and sits under the $20/month cap in ADR 0019. The build step stays unchanged: the server reads the file `make app-data` already writes, so there is no new pipeline and no second source of truth. A CI check (like `ci/check_export_fresh.py`) would verify the server's tool outputs against the committed file.

### 6. Abuse and rate limits
- **Local stdio:** none needed; the user's own process, one file read.
- **If hosted later:** per-IP limit (e.g. 60 requests/minute, 2,000/day), `limit` hard-capped at 25, no bulk "list everything" tool, radius capped at 100 km, request bodies under 1 KB, no logging of queries beyond aggregate counts (no personal data stored), and the same kill-switch idea as ADR 0019 (a flag that turns the endpoint off). Scraping the whole dataset through the API is pointless since the full file is already public; the limits protect cost, not secrets.

## Alternatives
1. **Do nothing.** Zero cost. Assistants that browse can already fetch the page or `venues.json`, but the single-letter keys and 2.4 MB size make good answers unlikely, and nothing tells them what the data means.
2. **`llms.txt` + a short data dictionary + a small per-sport/per-region JSON slice** published on Pages. Costs an hour, $0, no server, no abuse surface, and helps every assistant that can fetch a URL. It covers most of the same need for free, but cannot do "nearest to me" queries.
3. **Hosted API** (REST or remote MCP). Most capable for non-technical users; the most to build and watch; highest risk of unplanned cost. Revisit only with evidence of demand and a rate-limit design agreed first.
4. **Local stdio MCP server** (this ADR's option): near-zero cost, but only reaches users comfortable adding an MCP server to their assistant, a small group.

## Go / no-go
- **Now: no-go** on building any server. Demand is unmeasured; the beta (December) will show whether people ask assistants for courts at all.
- **Do now, cheaply (separate small task, not part of this ADR):** alternative 2 (`llms.txt` + data dictionary), since it needs no decision beyond "publish a text file on Pages".
- **Go for local stdio** (alternative 4) if the beta or GoatCounter referrers show assistant-driven visits or direct requests, with sections 2-4 as the spec, built in a single session and covered by a no-personal-data test. Hosted stays no-go until a separate ADR sets limits and a budget.
- **Owner decision needed:** accept, reject or defer this ADR. Accepting it records the design above; it does not start any work.

## Consequences
- If accepted as written: CLAUDE.md "After beta" line becomes "Read-only MCP server (ADR 0023, proposed): decide after the beta; first publish `llms.txt` + data dictionary."
- Costs nothing today. A local server later adds one script, one test and one doc to maintain, and a promise that the field allowlist is reviewed whenever the export gains a column (`export_app_data.py` changes would need to update it).
- Risks accepted: a stale copy answering with old data (mitigated by `data_as_of` and the check-first note); an assistant paraphrasing "reported" as "confirmed" despite the labels (we can only supply the labels, not control the paraphrase).
