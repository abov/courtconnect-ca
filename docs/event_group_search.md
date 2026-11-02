# Events, leagues and groups search ("find your people")

Owner 2026-11-02: every state we add gets a pass that looks for events, leagues, get-togethers and groups, so players can find their people. ADR 0028 makes it part of each state's step. Public organizer pages only; no Pickleheads, Places2Play or other court-app data (CLAUDE.md); aggregator listings (Bounce, MyPickleballConnect, Active.com, padelbrowser) are leads until the organizer's own page confirms them.

## Recipe (per state)
Standard searches only, about 5-10 per state, then read the organizer's own page for every hit.
1. Tournaments and sectionals, all sports: state pickleball, tennis, padel, table tennis, badminton, squash, racquetball. Rows go to `watch_events.csv` (dates in the future, https link, `dates_not_confirmed` if tentative). National-body section pages (USTA section, USA Pickleball, USA Table Tennis, USA Badminton, USA Padel) show next year's dates late: note "not yet posted" rather than guessing.
2. Recurring get-togethers: open play, club nights, mixers, ladders, round robins, juniors. One row per series in `social_events.csv` (`kind`: open_play, club_night, meetup, mixer, social_night, match_play). Fill `age_focus` and `audience` only when the organizer states them.
3. Leagues: a league run by a venue goes in `venue_actions.csv` as `league` (needs a map venue id); a league run by a group (Meetup, section league) is named in that group's `player_groups.csv` evidence.
4. Groups: Meetup, WhatsApp, Discord, Facebook and club pages in `player_groups.csv` (link only, never opened for WhatsApp). Meetup pages are public; read the group page for members and upcoming events.
5. Park districts and rec departments: adult leagues, drop-in and lessons (a slot for step 3).
6. Log below what was searched and what came back empty, so the routines (Parts 3-4, `docs/tournament_run_parts.md`) know what to recheck for the state.

## Oregon (2026-11-02)
Searched: pickleball, padel, tennis (USTA PNW), table tennis, badminton, Meetup groups, THPRD, Bend Park and Rec, Portland Parks and Recreation.
- **Added:** Learn Pickleball PDX (Meetup group and recurring open play at Hillside Community Center), TennisPortland / Portland Tennis League (Meetup), Portland Table Tennis Club (competition nights), Foundry Padel (Foundry Open Dec 5-6 2026, Foundry League Nov 2 - Dec 13 2026, open play), Oregon Indoor Pickleball Championships (Salem, mid-November 2026).
- **Not posted yet:** USTA PNW 2027 sectionals (usta.com page lists 2026 only; Aug 2026 Adult 18+ was in Portland); Bend Pickleball Club "2027 Pacific NW Classic" (page has no dates); THPRD winter 2027 adult pickleball league at Babette Horenstein Tennis Center (divisions "to be determined"); Portland Paddlers (Major League Table Tennis) 2026-27 home dates (mltt.com event page 404).
- **Past, not added:** Fall Brawl at Pickleball Kingdom (Tualatin, Oct 11-18 2026), TPC Summer Tussle (Jul 2026), Beaverton Bash (Jun 2026), Oregon Senior Games table tennis (Aug 2026), USTA PNW 55+ (Eugene, Jun 2026).
- **Empty:** badminton (no Portland or Oregon club or open-play page found), Salem and Eugene pickleball clubs (only aggregator listings), squash and racquetball (not searched this pass), Bend padel (Bend Racket Club has no site or dates). Padel PDX and UP Padel Club are listed on padelbrowser only.
- **Recheck next cycle:** Bend Pickleball Club `/upcoming-events/` (events live in CourtReserve), usta.com PNW sectionals page, THPRD Winter 2027 guide, mltt.com schedule.
