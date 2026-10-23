# 2026-10-22: shortlist Q&A and "court" dropdown idea

- Shortlist: saved in the visitor's `localStorage` (`cc.shortlist`, max 30, no expiry, no server). A saved venue missing from `venues.json` is skipped silently. Not checked: whether venue ids (`vid[:10]` in `export_app_data.py`) stay stable across refreshes.
- Idea (owner, parked): a second dropdown next to "sport" that narrows to what fits the chosen sport. Venue names are better served by search and the popup's sports list; the useful version is court type (indoor/outdoor, surface, walled, shared lines), shown only after a sport is picked.
- Next, only if wanted after beta: count how many venues have each court attribute per sport and whether it is confirmed or inferred; build only if coverage is good. No code changed.
