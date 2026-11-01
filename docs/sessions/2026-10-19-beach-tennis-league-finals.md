# 2026-10-19 Beach tennis league finals days

- Owner asked for the league finals days to be on the map. Added two amateur events from the organizers' own pages: BT Cali Club League 3rd Edition semifinals and finals (Sat Nov 7, Manhattan Beach 7th St) and Beach Tennis Santa Monica League 3rd Edition Finals Day (Sat Nov 14, Tower 26, top 4 per division). Both are finals days of a league, so they are labelled that way and say spectator access is not stated. The BTSM finals day has no published start time.
- Rule change in `docs/beach_tennis_watch.md`: a league's finals day is an event; the league season is not.
- Next: recheck the beach tennis organizers in early November for December / 2027 dates.
- Scheduled run: the existing task `courtconnect-tournament-refresh` (1st and 15th, next run 2026-11-01) now also reads the USA Padel calendar, the LA beach tennis organizers, the Instagram sweep and social handles for new venues. Details live in the repo (`docs/tournament_refresh.md`, last section; `docs/beach_tennis_watch.md`; `docs/instagram_sweep_snippet.js`), so the task only works once this PR is merged to main. Suggest "Run now" once to pre-approve the browser tools.
