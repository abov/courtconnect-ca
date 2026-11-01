# 2026-10-20 Play-anywhere notes: sheet court sizes and gear

- Owner: a sport with a fixed `court_dim` in the sheet needs a marked court to be played properly, so "needs no fixed court" was wrong for Road Tennis (21x10 ft, low net). Its note now says it needs a marked court on a flat surface and the map pins none yet. Crossminton (two 18x18 ft squares 42 ft apart) now says the squares are marked out for the game, so it still works anywhere.
- Owner: gear/kits are needed at the "anywhere" places too. Every row in `transform/seeds/sport_play_anywhere.csv` now ends with a "Bring your own ..." line from the sheet's `base_gear` (plus net, board or markers); sports with `gear_avail_ao = N` also say the gear is hard to buy.
- Build 253 pass, `venues.json` re-exported. Next: if the owner wants Road Tennis courts pinned, it needs real venues (none known); otherwise nothing.
