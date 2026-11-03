# Hawaii resort and hotel courts

Read 2026-11-02. The owner closed Nevada resort and casino courts (2026-10-17). For Hawaii the owner decided on 2026-11-02 to add resort courts as members / private (ADR 0028). Each resort has a `confirmed` row in `transform/seeds/venue_leads.csv` (`hi-*` lead ids) and 16 `manual_venues` rows (`hi-resort-*`, one per sport). Access is what the page supports: `private` = resort guests or eligible patrons (Fairmont Orchid, Mauna Lani, Turtle Bay, Hale Koa; non-guest play is not stated); `members` = members and guests (Holua, Hanalei Bay, Royal Kona); `club` = pass or drop-in fee sold to visitors, so not shown as members only (Royal Lahaina, Kapalua, Wailea). Counts are only what the source page states; directory counts are noted as unverified. Fairmont Orchid (page text did not load) and Royal Kona (page 403) are `reported`; Kapalua rests on a news article.
Three link-outs (`venue_actions.csv`, `hi-resort-*`): Royal Lahaina passes, Wailea daily court fee, Kapalua drop-in rates. No events were added.

| Resort | Island, city | Sports (as stated) | Who may play | Source (read 2026-11-02) |
|---|---|---|---|---|
| Royal Lahaina Tennis Ranch | Maui, Lahaina | Tennis; court count and pickleball not on the page (directories: 11 courts, 2 blended for pickleball) | Public with a daily, monthly, 3- or 6-month pass | [USTA Hawaii](https://www.ustahawaii.com/news/2024/2/8/the-royal-lahaina-tennis-ranch-is-open-for-business) |
| Kapalua Tennis Garden | Maui, Kapalua | Tennis and pickleball; counts not stated | Visitors: drop-in $25, or $18 for 90 minutes without membership; clinics, lessons | [Maui Now, Jan 2026](https://mauinow.com/2026/01/07/kapalua-tennis-garden-announces-tennis-pickleball-programming-and-rates/) (news, not the resort) |
| Wailea Tennis Club | Maui, Wailea | 9 or 11 tennis courts (the page says both); no pickleball listed | Daily court fee $30 ($17 with Hawaii ID); memberships, clinics, lessons | [waileagolf.com](https://www.waileagolf.com/tennis) |
| Fairmont Orchid (Hawaii Tennis Center) | Hawaii, Kohala Coast | 10 tennis courts and 2 pickleball courts, per a search result of the resort page (page text did not load on fetch) | Not stated; clinics, lessons, rentals | [fairmont.com](https://fairmont.com/orchid-hawaii/activities/tennis) |
| Mauna Lani Sports Club & Tennis Garden | Hawaii, Kohala Coast | Tennis, pickleball, cardio tennis; counts not stated | Court use is in the resort fee, so guests first; public not stated | [auberge.com](https://auberge.com/mauna-lani/wellness/tennis-pickleball/) |
| Holua Racquet and Paddle Center | Hawaii, Kailua-Kona | 7 lit tennis courts plus stadium court; 20 pickleball courts (8 lit) | Members; open play "welcomes all levels", fees on a page not read | [holuaracquetandpaddle.com](https://www.holuaracquetandpaddle.com) |
| Royal Kona Resort Tennis Club | Hawaii, Kailua-Kona | Own page unreadable (403); a USTA sectional venue | Unknown | [USTA Hawaii](https://www.ustahawaii.com/league-championships) |
| Turtle Bay Resort | Oahu, Kahuku | 4 tennis courts, "new" pickleball courts (no count) | Guests get 1 free hour; non-guest access and fees not stated | [turtlebayexperiences.com](https://turtlebayexperiences.com/things-to-do/pickleball-tennis) |
| Hanalei Bay Resort | Kauai, Princeville | 4 turf + 2 hard tennis courts, 6 pickleball courts | Registered guests and tennis members; public not mentioned | [hanaleibayresort.com](https://hanaleibayresort.com/tennis/) |
| Hale Koa Hotel (Fort DeRussy) | Oahu, Honolulu | Tennis and pickleball; count not stated | Military ID only (not public) | [halekoa.com](https://www.halekoa.com/experiences/activities) |

## Not read, not logged as leads
- **Grand Hyatt Kauai, Poipu:** the Hyatt page returned 403; only third-party listings (2 to 4 courts; Frommer's says guests only).
- **Hickam / Joint Base Pearl Harbor-Hickam:** no source found that names courts or who may use them.
- Official pages for Royal Kona (403) and a readable Fairmont text were not obtained; Royal Kona is a lead only because USTA names it as a venue.

## Held events at resorts (USTA Hawaii Pacific, [league-championships](https://www.ustahawaii.com/league-championships), read 2026-11-02)
Not added to `watch_events.csv` (they are team league play at resorts now on the map; add if wanted).
- Adult 65 and Over: Nov 14-15 2026, Royal Lahaina Tennis Ranch
- Tri-Level: Dec 5-6 2026, Fairmont Orchid
- Mixed 55 and Over: Dec 12-13 2026, Royal Lahaina Tennis Ranch
- Ekolu: Jan 9-10 2027, Royal Lahaina Tennis Ranch
- Dates, courts and facilities "may change" per the page. These are league play for registered teams; spectator access is not stated. Mixed 40 and Over (Sept 26-27 2026, Royal Kona and Fairmont Orchid) has already passed.

## Left open
- Fixed 2026-11-02: Royal Lahaina's second Overture record (wrong coordinates in Lahaina town) is linked to the ranch's court group in `place_venue_link.csv`, so the stray pin is gone.
- Hale Koa's tennis courts are not located separately; Hanalei Bay's pins sit at the geocoded address, not the courts.
- Grand Hyatt Kauai and Hickam are still unread; add them the same way if wanted.
