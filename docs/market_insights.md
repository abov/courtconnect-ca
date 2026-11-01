# Market insights (v1): where is a racket sport missing, who competes nearby

For clubs, operators and players. Built from the venues we already know; nothing new is scraped. Everything here is **inferred**: known venues only (private clubs are undercounted), distances are straight-line miles (not drive times), and there is no population data yet.

## How to use it
Run `make build` (or `make fresh-db` in a new worktree), then query the DuckDB file `courtconnect.duckdb` (`view_db.bat`, or Python: `duckdb.connect("courtconnect.duckdb", read_only=True)`). Three starting points:

```sql
-- Operator: cities with plenty of racket activity and no known padel venue within 15 miles
select city, racket_venues_in_city, nearest_mi
from marts.mart_market_gaps
where sport_name = 'Padel' and gap_status = 'no_venue_within_15mi' and racket_venues_in_city >= 20
order by racket_venues_in_city desc;

-- Club: how crowded is my sport around my venue?
select venue_name, sport_name, same_sport_venues_5mi, same_sport_venues_15mi, nearest_same_sport_mi
from marts.mart_venue_neighbors
where venue_name ilike '%your club%';

-- Player: other sports within reach of a venue
select sport_name, venues_within_5mi, venues_within_15mi, nearest_mi
from marts.mart_venue_nearby_sports
where venue_id = '<venue_id>' order by nearest_mi;
```

### Ask in plain English (free, local)
`python ingestion/ask.py "where is padel missing near big racket cities?"` sends the question to a free local model ([Ollama](https://ollama.com): install it, then `ollama pull qwen2.5:3b`; set `OLLAMA_MODEL` to use another). The model only **picks one of five vetted queries** (`--list` shows them) and fills in its parameters; it never writes SQL, so it cannot return a made-up number or touch the data. The query, its parameters and the inferred caveat are always printed, and the database is opened read-only. Nothing leaves your machine. Without Ollama, run a template directly: `python ingestion/ask.py --template sport_gaps sport=Padel min_racket_venues=30`. Needs `courtconnect.duckdb` (`make build`). The model step has not been run against a real model yet; the templates and the parameter checks have.

To share a result, export it from DuckDB to CSV (`copy (...) to 'out.csv'`) and say it is inferred, with the date of the build.

## The tables (all in `marts`)
- `mart_market_gaps`: one row per city x sport. `gap_status` is `served` (a venue in the city), `nearby` (none in the city, one within 15 miles) or `no_venue_within_15mi`. `racket_venues_in_city` is a rough activity proxy. The city point is the average of its venues' coordinates.
- `mart_venue_neighbors`: per venue and sport, how many other venues offer that sport within 5 and 15 miles (the competition a club faces).
- `mart_venue_nearby_sports`: per venue, the sports it does not list that exist within 15 miles, with the nearest (the "try another sport" list). No row = none within 15 miles in our data.
- `docs/market_snapshots.csv`: city x sport counts, appended at each refresh by `make market-snapshot`. The warehouse is rebuilt every time, so this file is the only history; it turns openings and closures into a trend.

Only sports a venue is directly listed for count. Sports that exist only as an inference (`sport_also_played`, e.g. Frescotennis on every tennis court) are left out, or they would inflate every number.

## How to read a gap
Check `sport_coverage_status` (from `mart_sport_gaps`) first: for a `sparse` or unmapped sport, "no venue within 15 miles" can mean we have not found it, not that it is absent. Padel is `covered` by that rule (37 venues, 29 hand-added), so a padel gap is meaningful but still a lower bound on supply.

Example (2026-10-23 build): padel has no known venue within 15 miles of 65 cities that have 20+ racket venues, including Malibu, Irvine, Napa, Santa Rosa and Newport Beach. Treat that as a list of places to check, not a market sizing.

## Known limits (next)
- No population, so no per-capita figure. v2: Census ACS by place/tract (free), then "people per court".
- A few cities have junk names from upstream address data (e.g. `1-WS-1`, 3 of 888); Overture's capitals ('IRVINE') are merged with OSM's ('Irvine') here, not upstream.
- Sub-variants (eight Basque Pelota forms, etc.) each get their own rows; filter by `popularity_class` before showing a business anything.
- Not in the app, not in `venues.json`. Decide where it goes after the beta (ADR 0015).
