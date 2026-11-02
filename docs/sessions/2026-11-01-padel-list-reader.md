Added `ingestion/read_usa_padel_list.js` (headless Chromium reads the official USA Padel list, which `padelusa.org/calendar` and plain fetches cannot); fixed Padel N9NE Nov 2026 to Nov 14-15 and re-dated 3 rows read this day; cloud preflight now uses `gh api` not `gh auth status`.
Taktika San Diego / Park Padel South SF Dec 11-13 are not in the official list: moved to `venue_leads.csv` 2026-11-02 (owner OK).
Next: BTCC finals page 404 and the Instagram-only Southwest Regional still need a person; consider an "unreadable source" status (needs an ADR).
