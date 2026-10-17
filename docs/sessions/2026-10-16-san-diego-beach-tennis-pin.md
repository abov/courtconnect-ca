# 2026-10-16 San Diego beach tennis pin

- Added `sd-brighton-ave-ocean-beach` (Beach Tennis, `reported`) to `manual_venues.csv`: owner-reported from the group's public Facebook page, courts at 5172-5188 Brighton Ave, San Diego (geocoded to 5172, OSM). Replaced an earlier Mission Beach / Tower 22 pin (San Diego Reader, 2018, stale); no other beach tennis pins exist in the San Diego area. Lead `beach-tennis-mission-beach-tower-22` marked resolved. Full dbt build passes on DuckDB.
- NOT done: `app/data/venues.json` is not regenerated. This worktree's DuckDB copy has stale/missing raw tables (walls fell 901 -> 276), so an export from it would regress the map. Run `make app-data` from a fully loaded DB, commit venues.json, then re-run `pages.yml`.
- Next: read the group's public Facebook/Instagram (`beachtennissandiego`) as text; if it shows current sessions, raise the pin to `official` and add a social link-out row (ADR 0009).
