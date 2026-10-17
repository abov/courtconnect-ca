# 2026-10-16 San Diego beach tennis pin

- Added `sd-mission-beach-zanzibar-ct` (Beach Tennis, `reported`) to `manual_venues.csv` from the San Diego Reader, 2018-08-07 (PlayBT Beach Tennis San Diego group at Tower 22 / Zanzibar Court); location approximate (OSM geocoder, beach end of Zanzibar Court). Lead `beach-tennis-mission-beach-tower-22` marked resolved. Full dbt build passes on DuckDB.
- NOT done: `app/data/venues.json` is not regenerated. This worktree's DuckDB copy has stale/missing raw tables (walls fell 901 -> 276), so an export from it would regress the map. Run `make app-data` from a fully loaded DB, commit venues.json, then re-run `pages.yml`.
- Next: read the group's public Facebook/Instagram (`beachtennissandiego`) as text; if it shows current sessions, raise the pin to `official` and add a social link-out row (ADR 0009).
