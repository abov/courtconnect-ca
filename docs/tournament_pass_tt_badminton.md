# Table tennis and badminton pass (2026-10-19)

Catch-up for the clubs only added as link-outs in PR 272. Rules: ADR 0009 and its 2026-10-19 amendment. A separate file so it cannot collide with `tournament_sources.md` (Pass 9 is there).

## New source: the Omnipong tournament list
`https://omnipong.com/t-tourney.asp?e=0` is public and needs no login (the "Enter" links do). It lists every USATT-sanctioned and many unsanctioned US table tennis tournaments with name, city, dates, star level and organizer, grouped by region (the California block is about 60 rows). Parse it with `fetch` from a page on the same origin (a cross-origin fetch fails) and read the `<tr>` cells. The entry-form PDFs download instead of opening in the browser pane, so the venue is not readable there: use the organizer's own site for the venue and for any date that differs. Add it to the scheduled refresh. Not added this pass (city only, venue unknown): LATTA monthly opens (El Monte), FMQTTA Winter Open (Fullerton, Nov 7-8, 3-Star), Sacramento Fall Fun Giant RR (Nov 7, 3-Star), ASLT San Diego (Nov 6-7), Anaheim Senior (Nov 21-22), Long Beach TTC 94th Anniversary (Mar 20-21 2027), and OCTTA/ICC events after March 2027.

## Instagram sweep (SINCE 2026-10-01)
| Account | Result |
|---|---|
| @888tabletennis | Silicon Valley Open 2026 registration post (Oct 16); event added from the Omnipong listing. NorCal Challenge Series Nov 1 added from 888ttc.com. USATT California Open (Oct 9-11) is past. |
| @bayareatt | Only league results at ICC (past). ICC events taken from icctt.org and Omnipong. |
| @synergybadminton | Grand Opening mini-tournament Oct 24 uses `#apexnc` and no California address on the site: not added. Thanksgiving camp (Nov 23-27, Fremont) is a camp, not an event. A second Fremont site (Mission Blvd) became a lead. |
| @southbaytt, @ttamerica, @santacruztabletennisclub, @mmtta2019, @badmintonalley, @shuttlbadminton, @californiatabletennis, @gilbertttc, @littletokyotabletennis | No upcoming tournaments in the recent posts (classes, results, camps). @gilbertttc, @californiatabletennis and @mmtta2019 have not posted since 2022-2025. |
| @fremonttta | The profile returned no post links logged out (two tries); the club's own tournaments page was read instead. |

## Club websites
- fremonttabletennis.com/tournaments: Thanksgiving Teams Nov 28-29 at the Silliman Activity Center, Newark (Omnipong says Nov 27-29; the club's dates are used). Oct 16-18 Open is past.
- icctt.org/upcoming-tournaments: JOOLA Autumn Open Oct 24-25; the page says a $10 gate fee applies on Sunday for non-players (stale August date on the page).
- octabletennisacademy.com/tournament-schedule: Autumn Open Oct 24-25 (matches Omnipong); Winter Open Dec 19-20 (Omnipong says Dec 26-27, so `dates_not_confirmed`).
- smashbsd.com (SMASH Badminton San Diego): only past tournaments. pongplanet.com: no tournaments page loads. mmtta.io: none. lttt.life: none. Fresno Badminton: Google Sites FAQ only (not read for events).
