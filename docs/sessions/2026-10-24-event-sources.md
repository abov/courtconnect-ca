# 2026-10-24 Event source list

Added `docs/event_sources.csv` (every site the tournament runs read, with status and last_checked/last_yielded), `ci/check_event_sources.py` (CI: an event may only link to a listed site) and a "Finding new event sites" step in Part 2 (one standard search per sport, read candidates, mark active/rejected). Four candidates are unread: usracquetball.org, tournamentsoftware.com, pickleballbrackets.com, eventbrite.com.
Next: the first Part 2 run reads those four; `last_checked` is blank for most rows until a run sets it.
