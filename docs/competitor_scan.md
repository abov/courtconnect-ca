# Competitor scan and community recommendation (2026-10-16)

Read from each app's public page on 2026-10-16 (Playo from general knowledge: its Play Store page did not load). Re-check before quoting numbers.

## Who does what
| App | What it does | Sports | Money |
|---|---|---|---|
| Places2Play / Pickleheads | Court directory; Pickleheads is now USA Pickleball's official court and game finder | Pickleball | Pickleheads has paid extras |
| Playo | Venue booking plus finding players, mainly India | Many | Booking fees |
| Playtomic | Club court booking plus level-based matchmaking | Padel, tennis, pickleball | Court fees |
| GoodRec | Hosted pickup sessions, a host at each game; 70+ cities | Soccer, volleyball and more | Pay per session |
| Plei | Pickup games; 500K players in 26 US regions | Soccer only | Pay per game |
| OpenSports | Organizer software: leagues, waitlists, payments, memberships | Organizer's choice (incl. pickleball, badminton) | Organizer fees |
| Gameli / Meetup | General "find people" apps and groups | Anything | Free |

**Data:** Places2Play is behind a sign-in, and Pickleheads' terms forbid bot access and compiling a directory from the site. Neither
is a data source. No partnership emails until we are ready to socialize or monetize.

## Player-matching apps scan (2026-10-21, social phase A)
Read from public App Store pages and the connectplayers.ca home page (text only, no logins). Terms of service NOT read for any of them; we only link out, nothing is scraped or stored.
| App | Sports | Price | Region evidence |
|---|---|---|---|
| Hitch | Tennis, padel, pickleball | Free + paid plans | Lists Los Angeles among its cities |
| Courtmate | Tennis, padel, pickleball | Free + paid plans | None stated |
| Matched Point | Tennis, pickleball | Free + paid plans | "Live in your city", none named |
| Padel Mates | Padel, pickleball, tennis, badminton, squash | Free + paid Pro | None stated |
| ConnectPlayers | Badminton, tennis, pickleball, table tennis (20+) | Not stated | None stated (.ca domain) |
| Playtomic | Padel, tennis, pickleball | Player prices not stated | None in CA/NV (Miami is the only US club shown) |
| UTR Sports | Tennis, pickleball | Free signup + paid subscription (search summaries; page body did not load) | None checked |
| PairUp | Tennis, padel, pickleball | Free; league fees via Stripe | None stated; 5 ratings |
| RacketPal | Tennis, badminton, squash, table tennis, padel | Free + premium | London origin (2019); no US region stated |

Added later the same day (2026-10-21): Playtomic, UTR Sports, PairUp and RacketPal, from public store and homepage text. Not added: the names "Link Up" and "RacketX", which could not be found at all. Re-check if the owner has a link. None of the five has a verified California/Nevada player pool, so the app says so. Shown as the "Find people to play with" list (seed `player_platforms.csv`, needs `evidence` + `verified_on`). Next: filter the existing Meetup/WhatsApp/Partiful link-outs into the same view; deep links or embeds need the platform's say-so, so no.

## What makes CourtConnect different (keep these)
1. **Every place, not only bookable ones:** public parks, hitting walls, YMCAs, rec centers, places to watch.
2. **Every racket sport**, with room to discover lesser-known ones; tennis stays visible next to pickleball (ADR 0015).
3. **Honest labels:** reported / official / visited with dates. Stale data is the known weak spot of Places2Play.
4. **Links out, never books or takes payments:** a GoodRec session, an OpenSports league or a Playtomic court can be a link-out on our pin.

## Should we build a player community like Plei's?
Not that model: hosted games, payments and dense players per city need staff, safety and moderation work, and start empty (Gameli's
own guide says you may have to host the first game). Instead:
- **Now:** community around the data: word-of-mouth reports shown as `reported` (`docs/community_reports_plan.md`).
- **Social phase A (closed 2026-10-21):** a "community of communities": link-outs to player apps and recurring open-play series that already exist
  (Watch & Social view). Each app's terms are still unread; we only link out.
- **Only if the beta shows demand:** phase B (own profiles and matching), with its own ADR. Signals: GoatCounter clicks on social
  link-outs, and a beta question such as "Would you use CourtConnect to find people to play with?"

Sources: [Gameli guide](https://www.gameli.app/guides/best-apps-to-find-people-to-play-with),
[Plei 2.0](https://www.plei.com/blog/meet-plei-2-0-building-the-largest-soccer-community-in-the-world),
[OpenSports](https://opensports.net/), [GoodRec](https://apps.apple.com/us/app/goodrec/id1510554246),
[Playo](https://play.google.com/store/apps/details?id=com.techmash.playo), [USA Pickleball](https://usapickleball.org/places-to-play),
[Pickleheads terms](https://www.pickleheads.com/terms).
