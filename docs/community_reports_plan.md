# Community reports: plan (2026-10-16)

Status: step 1 BUILT and merged (#149); step 2 BUILT (2026-10-16); step 3 PARKED by the owner (2026-10-16) for later; setup below is ready when picked up.

## Why
The owner can't visit venues, and court-finder apps are off limits (Places2Play needs a sign-in; Pickleheads' terms forbid
compiling a directory from its site). Growth therefore comes from public pages plus **word of mouth from CourtConnect users**.
ADR 0008 already makes `reported` the lowest level and says two independent confirmations raise a venue. Three things block it today:

| Gap | Today |
|---|---|
| 1. GitHub login needed | All three report forms are GitHub issue forms. Most players have no GitHub account. |
| 2. Reports on existing venues never reach the map | `ci/issue_to_pr.py` can only address `manual_venues` rows. A report on an Overture/OSM venue (most of the map) becomes a lead, and leads are hidden. |
| 3. Report count only half there | The export already sends `cn` (distinct confirmers) and the popup shows "N people confirmed", but only for manual venues, `venue_confirmations.csv` is empty, and `method` allows only `visited` / `official`. |

## Cheapest design: every approved report becomes a manual venue row
The build already merges a `manual_venues` row into the nearest matching venue within `manual_match_radius_m`
(`int_manual_venue_match`), with `manual_venue_no_merge` as the escape hatch. So a report on an existing venue can be written
as a `manual_venues` row **at that venue's coordinates** with `confirmation = reported`. It then merges into the existing pin.
No new model, no new join, and the `cn` count works through `venue_confirmations`.

Map IDs (`v.i`) are not stable keys: OSM venue ids are `md5(cluster_label)` and change when clustering changes (the 10-16 dedup did
this). So the script uses the map id only once, at approval time, to look up name + coordinates in `app/data/venues.json`. After that
the stable key is the new `manual_venues.venue_key`.

## Steps (each its own small PR)
**Step 1. Reports on existing venues reach the map** (~40 lines in `ci/issue_to_pr.py`, no model change). BUILT: new form option
"Report a racket sport played here" + "Sport played here" field; `venue_confirmations.method` accepts `reported` (not counted in the map's `cn`);
warn test `assert_reported_pins_merged`; `venue_leads.source_type` accepts `issue` (the script always wrote it). Simulated 5 reports:
both pins merged (venue count unchanged), badge 'Reported', Pickleball added at Willow Glen.
- "Report a sport/courts here" or "Confirm" on a non-manual venue: look up the map id in `venues.json` and append a `manual_venues` row
  (name, sport, city, lat/lon from the pin, `location_precision = pin`, `confirmation = reported`, evidence = issue text + date).
  Also append a `venue_confirmations` row (`method = reported`) for the reporter.
- Corrections and closures stay leads (one unverified report must not remove a venue). A closure needs two reports or an official page.
- Check: `dbt build --select int_manual_venue_match+` and `assert_no_duplicate_venues`, then confirm in the export that the row merged
  onto the reported pin and did not make a second pin.

**Step 2. Count reports, not only confirmations** (staging + export + popup text, small). BUILT: export adds `rn` (people who only
reported; someone who also confirmed counts once, as a confirmer); popup: "reported by N people", and on a venue still at `reported`
its confirmations read "N confirmations waiting for review" (not "confirmed by"); `make quality` prints venues reported by 1 and by 2+.
`method` already accepted `reported` (step 1). Also fixed the popup separator (a broken character since PR #7, now a middle dot).
- `stg_venue_confirmations.method` accepts `reported`; add an `accepted_values` test (`visited | official | reported`).
- Popup: "Reported by N people" when every row is `reported`, "Confirmed by N" otherwise. Count distinct `confirmed_by`.
- Level rule (ADR 0008, unchanged): 2+ independent reporters, or 1 report + an official page, may raise `reported` -> `official`
  (with a link) or `visited` (a reporter's dated visit). The reviewer decides in the PR. Nothing raises a level automatically.
- `make quality` gets one line: venues with 1 report, and venues with 2+.

**Step 3. Report without GitHub** (Google Form -> Google Sheet, reviewed in the sheet)
- One Google Form owned by the owner: venue, city, map id (prefilled from the popup link), what you saw, date, optional https link,
  optional "name or handle to credit you" (shown in git history like GitHub handles today). **No email field** and no sign-in, so no
  personal data reaches the repo.
- The popup gets a second link, "Report without a GitHub account", with a prefilled URL (Google Forms `entry.<id>=` parameters). GitHub stays for people who have it.
- The owner reviews in the sheet: adds `approved` in a review column (a plausibility and spam check only, since the owner can't visit).
- `make sync-reports` (new, read-only fetch of the sheet's CSV, like `make sync-sports`) runs the same row-writing code as
  `issue_to_pr.py` (refactor into a shared function) for approved rows not yet imported, then a normal PR. Run it at the twice-monthly
  sync, runbook step 2b, next to `make issues`.
- Anonymous rows: `confirmed_by = form:<sheet row>`. The reviewer judges independence. Two anonymous reports with the same wording or
  time count as one.

**Step 3 setup (owner, about 10 minutes; then one session builds `make sync-reports` and the popup link)**
1. Google Forms -> new form "CourtConnect: report a place to play". Settings: **Collect email addresses: off**, **Restrict to users in
   your organisation / require sign-in: off**, "Limit to 1 response": off.
2. Questions, with these exact titles (the import matches on them):
   - `Venue name` (short answer, required) - `City` (short answer, required) - `Map ID` (short answer, optional; the popup fills it)
   - `What are you reporting?` (multiple choice, required): `A racket sport is played here` / `I visited, or the operator's page says so` /
     `Something is wrong or it closed`
   - `Sport` (short answer) - `Date you saw it` (date, required) - `What did you see?` (paragraph, required)
   - `Link to a public page (optional, https)` (short answer) - `Name or handle to credit you (optional, shown publicly)` (short answer)
   - Description at the top: "Please don't include phone numbers, emails or other personal details. A reviewer checks every report."
3. Responses -> Link to Sheets (new sheet). In the response tab add two columns at the right: `review` (type `approved` or `rejected`)
   and `imported` (the import fills it in later; leave blank).
4. Add a second tab `approved` with `=FILTER(<response tab>!A:Z, <response tab>!<review column>:<review column>="approved")`
   so only approved rows are read. Share the sheet as "Anyone with the link can view" (the id stays private in `.env`, like the
   sports sheet).
5. Send me: the form's link, one prefilled link (Form menu -> "Get pre-filled link", fill Venue name / City / Map ID with `X`), and the
   sheet id + the `approved` tab's gid. They go in `.env` as `REPORTS_SHEET_ID` / `REPORTS_SHEET_GID`, the prefilled link in the app.

## Not in scope (later)
- Comments shown publicly on the map, accounts, upvotes, or a backend. These need the social-phase-B ADR (ADR 0015) and beta demand.
- Partnership or data-licence emails: deferred until the owner is ready to socialize or monetize.

## Docs to update when built
ADR 0008 ("Update: community reports" section), `CONTRIBUTING.md` (the no-GitHub route), `docs/monthly_refresh.md` step 2b,
README roadmap line.

## Effort and order
Step 1 then 2 (one session each, small). Step 3 needs the owner to create the Form (about 10 minutes, steps written when we get there) and one session.
Suggested order: 1 -> 2 -> 3, or 3 first if the beta round (replies due 10-28) shows that the GitHub login is what stops people.
