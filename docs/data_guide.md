# Data guide: sources, seeds and editing

Detail moved out of the README. Live numbers: `docs/coverage_snapshot.md` (`make report`) and `make quality`.

## The sports list (`all_racquet`)
The Google Sheet tab **All Raquet** is the source of truth for the supported sports. `make sync-sports` pulls it into
`transform/seeds/all_racquet.csv` (needs `SPORTS_SHEET_ID` in `.env`); `dim_sport` cleans it.

- Edit the sheet only. Never hand-edit the CSV: the next sync overwrites it.
- The owner account can edit; "anyone with the link" is view-only, which lets the sync read it without a login. Share as *Editor* to add a second editor.
- Run the sync at every twice-monthly project sync (`docs/monthly_refresh.md` step 2) and carry renames or new sports through seeds, scripts and the app.
- Alternate names (e.g. "Frescobol" for Frescoball) go in `transform/seeds/sport_aliases.csv`. Sports OpenStreetMap cannot find: `docs/sport_name_review.md`. Licenses: `NOTICE.md`.

## Seeds you edit (then `make build`, and `make app-data` for the map)
| Seed | Use it for |
|---|---|
| `manual_venues.csv` | Venues no dataset knows. One row per venue and sport, with coordinates, surface, setting, offers and an `evidence` note. Shown as `venue_source = 'manual'`; a test fails on mistyped coordinates. |
| `venue_actions.csv` | Link-outs: `open_play`, `clinic`, `private_lesson`, `group_class`, `drop_in`, `tournament`, `league`, `social_event`, `court_booking`, `club_page`. Provider's own link, price note, dates; keep `verified_on` + `evidence` (warning after 60 days). Overture places only. |
| `watch_events.csv` | Events to watch. https links only; tests reject bad coordinates and backwards dates. Past events hide themselves. |
| `place_sport_overrides.csv` | Confirm or reject uncertain matches ("Camino Real Tennis Center" is not Real Tennis). Queue: `marts.mart_places_to_review`. |
| `closed_places.csv` | Overture places that no longer exist but are still listed as open (`stg_overture_places` drops them). Needs `evidence` (owner report or public page) + `verified_on`. |
| `sport_aliases.csv` | Alternate sport names. |

Seed files must keep CRLF line endings. Seed column changes need `dbt build --full-refresh`.

## Pop Tennis (paddle tennis) map import
`ingestion/import_paddle_tennis_map.py` imports a hand-compiled West LA map (ID in `.env` as `PADDLE_TENNIS_MAP_ID`). Public and "in question" courts, plus private clubs and apartments (access `members`/`private`), are included; private homes never. Courts within 150 m of a known venue merge into it. Entries marked "?" show **Public access not confirmed**. Review the output before committing.

## Dead websites
About 10% of websites in the open places data point at domains that no longer exist. `make check-websites` runs a DNS-only check (no pages fetched) and sets `website_status` (`ok`, `dead`, `unknown`); the app-facing `website_usable` hides dead links. A site counts as dead only on a definitive "domain does not exist". See `marts.mart_website_quality`.

## Link-outs and providers
CourtConnect takes no registrations or payments; the provider does. `make check-links` confirms every link still loads. What was found about Playtomic, PlayByPoint, BracketSync and others: [ADR 0006](decisions/0006-watch-events-and-link-out-discovery.md).
