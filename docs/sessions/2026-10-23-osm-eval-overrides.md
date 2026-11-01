# 2026-10-23 OSM gold set + override check: no changes

- Gold set: not re-run. Raw `osm_courts*.csv` still 2026-10-14, `osm_parents*.csv` 2026-10-17 (only the wall/beach-volleyball scans are newer); standing result 129 pairs, 0 wrong, 4 missed.
- Overrides: read-only check of all 144 `osm_court_sport_overrides.csv` objects against live OSM (api.openstreetmap.org, project User-Agent). One fix has landed: Jim Gilliam ways 1562970254/5 now `paddle_tennis;pop_tennis` (edited 2026-10-15). The other 142 rows' objects are unchanged since the 2026-10-09/14 extract.
- Rows kept: our raw extract still says `padel` for those 2 ways, so dropping their rows now would put Padel back on the map. Drop them (and any others fixed by then) after the next OSM extract + `make load`, then re-run `make eval-match`.
