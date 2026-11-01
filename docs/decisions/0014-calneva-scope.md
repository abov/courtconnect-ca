# 0014. CalNeva scope: California + Nevada

Date: 2026-10-14. Status: accepted (2026-10-14); steps 1-4 done (regions table #65, region column #67, labels, Nevada extracts: 525 NV venues live as of 2026-10-17). Step 5 (Nevada seeds, leads, runbook) is done as of 2026-10-21: Reno, Henderson, Clark County and Washoe County parks seeded, Las Vegas events and social series in, the runbook covers both regions through the `REGIONS` table; Sparks parked; NV resort and casino gyms closed by the owner 2026-10-17. The 8 open NV leads wait on outside events (recheck January 2027). Open question 1 is answered: the repo and Pages URL stay `courtconnect-ca` (owner 2026-10-23, no rename planned). The "Engines" line below is superseded by ADR 0018 (DuckDB only).

## Context
CourtConnect covers California only. The owner wants the same coverage for Nevada (Las Vegas/Henderson, Reno/Sparks, Carson City, Lake Tahoe) and the product to be called "CalNeva". `docs/calneva_audit.md` lists every hard-coded California assumption (extract borders and boxes, two bbox tests, the `likely_in_california` flag, map bounds, labels). Nothing in the models or export carries a state today.

## Decision
- **Scope:** two regions, `CA` and `NV`. Everything done for California is repeated for Nevada: OSM/Overture extracts, seeds, sport mappings, tournaments and watch events, link-outs (ADR 0009/0010/0012), walls, quality scorecard, freshness runbook. The same rules apply (public pages only, ADR 0005 and 0007, honesty labels, link out only).
- **Region key:** a `region` column (`CA`/`NV`), set at the raw layer by the extractor and verified against the state border polygon, not address text (often missing). One venue has one region. It is carried through `dim_venue`, the mart and the export so the app can filter and label by state.
- **Regions table:** `ingestion/overpass.py` gets one table (code, bounding box, OSM border relation id, cache file) replacing the California-only `BBOXES`, `california_tiles`, `california_border` and `in_california`. Nevada metro boxes are added. Extractors take `--region` / `--area` for either state. The California border relation stays 165475; the Nevada one is looked up and checked before use.
- **Border clip stays the real filter.** Bounding-box tests become "inside CA or NV" sanity checks only. Near Tahoe and Stateline the boxes overlap, so tests use known points on both sides of the border.
- **Labels:** user-facing and doc text says "CalNeva" where it means the covered region (app title, description, header, map label, Makefile help, coverage report heading, README, docs). Historical text stays: ADRs 0001-0013, past status lines, and California-only source lists in the tournament docs (Nevada rows are added beside them).
- **Names kept stable:** repo, folder and Pages URL (`courtconnect-ca`) do not change (owner 2026-10-23: no rename planned).
- **Order:** (1) region table and polygon clip with a check on known CA/NV points; (2) `region` column through raw, dim, export and app; (3) one PR renaming labels; (4) Nevada metro extracts (slices first, as for walls, statewide later); (5) Nevada seeds, tournaments, leads and runbook rows.
- **Engines:** (superseded by ADR 0018, 2026-10: DuckDB only, no Snowflake target) a seed that gains a column still needs a full refresh.

## Open questions (owner)
- Is "CalNeva" only the app and doc name, or also the repo and domain?
- Do quality targets (e.g. named venues 25%) apply per region or combined?
- Are Nevada sports outside the Google Sheet needed? (They would be added there, never by hand in `all_racquet.csv`.)

## Consequences
Roughly doubles the area to keep fresh, so the monthly runbook and the 35-day freshness SLA must cover both regions. Coverage numbers will drop at first, since Nevada starts with OSM and Overture only and few hand-checked venues, and the scorecard should show per-region figures so California's quality is not hidden. Honesty labels are unchanged: Nevada rows are inferred or reported until a public page confirms them.
