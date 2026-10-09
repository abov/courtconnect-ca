# Sport name review

The master list (`all_racquet`, synced from the Google Sheet) has 75 racket sports. OpenStreetMap (our first court source)
has a tag for **22** of them. This is the list of the **53 that are not on the sport map**, and why.

**How to read it.** "No OpenStreetMap tag exists" means the sport is real but nobody has a way to map its courts there, so we
need another source (Google Places keyword search, club directories, governing-body sites). It does **not** mean your
spelling is wrong. Rows that say "please check" are names I could not verify; those are the ones most likely to be
misspelled or to go by a different name.

If a sport goes by another name, add it to `transform/seeds/sport_aliases.csv`. Those alternate names are what the
Places / directory searches will use.

| # | Sport | Players | Why it is not on the map |
|---|---|---|---|
| 1 | Crossminton/Speedminton | 2-4 | Official name is 'Crossminton'; 'Speedminton' is the original brand |
| 2 | Teqis (bt/curved table) | 2 | No OpenStreetMap tag exists and no website listed |
| 3 | Teqpong (tt/curved table) | 2 | No OpenStreetMap tag exists and no website listed |
| 4 | Typti | 2-4 | No OpenStreetMap tag exists and no website listed |
| 5 | 1-wall Paddle (alt 3-wall/handball courts) | 2-4 | No OpenStreetMap tag exists and no website listed |
| 6 | Frescoball | 2+ | Common spelling is 'Frescobol' - add as alias |
| 7 | Kadima/Matkot (Isreal), Smashball (US), Raketa (Greece) | 2+ | 'Isreal' -> 'Israel'. Three different names in one cell: Matkot is the usual search term |
| 8 | Road Tennis | 2 | No OpenStreetMap tag exists and no website listed |
| 9 | Spec Tennis | 2-4 | No OpenStreetMap tag exists |
| 10 | Riftball | 2-4 | No OpenStreetMap tag exists and no website listed |
| 11 | Goodminton | 2-4 | Trailing space on the sheet (auto-trimmed) |
| 12 | Jazzminton | - | No OpenStreetMap tag exists and no website listed |
| 13 | Sandball (Beach Pickleball) | 2-4 | No OpenStreetMap tag exists and no website listed |
| 14 | Skyball | 2-4 | No OpenStreetMap tag exists and no website listed |
| 15 | Lite Tennis | 2-4 | No OpenStreetMap tag exists and no website listed |
| 16 | Tennis Baseball | 18 | No OpenStreetMap tag exists and no website listed |
| 17 | Xare (Similar to Basque Pelota) | 2-4 | No OpenStreetMap tag exists and no website listed |
| 18 | Naked Tennis | 2-4 | No OpenStreetMap tag exists and no website listed |
| 19 | Downside Ball Game | - | No OpenStreetMap tag exists and no website listed |
| 20 | Ball Badminton | 10 | No OpenStreetMap tag exists |
| 21 | String Paddleball | 1 | No OpenStreetMap tag exists and no website listed |
| 22 | Pang Pong | 2 | No OpenStreetMap tag exists and no website listed |
| 23 | Frescotennis | 2-4 | No OpenStreetMap tag exists and no website listed |
| 24 | Miniten Thug | 2-4 | Possible stray word in the name - please check |
| 25 | Jokari | 1-2 | No OpenStreetMap tag exists and no website listed |
| 26 | Speedball (similar tether tennis) | 1 | No OpenStreetMap tag exists and no website listed |
| 27 | Smolball | - | No OpenStreetMap tag exists and no website listed |
| 28 | Biraq (2 rackets, similar Bi-Rak-It) | 2-4 | I could not verify this spelling - please check |
| 29 | Australian Racquetball | 2-4 | No OpenStreetMap tag exists and no website listed |
| 30 | Tennis Triples (sim 3-Way Mini Tennis) | 6 | No OpenStreetMap tag exists and no website listed |
| 31 | Eclipseball | - | No OpenStreetMap tag exists and no website listed |
| 32 | Indiaca Tennis | 2+ | No OpenStreetMap tag exists and no website listed |
| 33 | Floor Pro Mini Tennis | - | No OpenStreetMap tag exists and no website listed |
| 34 | Rapidball (between squash and racquetball) | 2+ | No OpenStreetMap tag exists and no website listed |
| 35 | Taiji Bailong | 2 | No OpenStreetMap tag exists and no website listed |
| 36 | Ricochet | 2+ | No OpenStreetMap tag exists and no website listed |
| 37 | Street Racket | 2+ | No OpenStreetMap tag exists and no website listed |
| 38 | Loboton | 4+ | No OpenStreetMap tag exists and no website listed |
| 39 | Qianball (from Qianlongball) | 2-4 | Transliterated name - please check the spelling |
| 40 | Shuttleball | 2-4 | No OpenStreetMap tag exists and no website listed |
| 41 | Toccer (Tennis Polo) | 20 | No OpenStreetMap tag exists and no website listed |
| 42 | Knuckle Racket (boxing raquet) | 2+ | No OpenStreetMap tag exists and no website listed |
| 43 | Street Tennis | 2-4 | No OpenStreetMap tag exists and no website listed |
| 44 | Ketball | 2 | I could not verify this name - please check the spelling |
| 45 | Pro Sunball | 2-4 | No OpenStreetMap tag exists and no website listed |
| 46 | Wacquetball (wisperball, wimpy ball) | 2-4 | No OpenStreetMap tag exists and no website listed |
| 47 | Table Squash | 2-4 | No OpenStreetMap tag exists and no website listed |
| 48 | 360Ball | 2-4 | No OpenStreetMap tag exists and no website listed |
| 49 | Pitton | 2-4 | I could not verify this name - please check the spelling |
| 50 | Wall Pong | 2+ | No OpenStreetMap tag exists and no website listed |
| 51 | Racket Hockey | 4 | No OpenStreetMap tag exists and no website listed |
| 52 | Micro Pickleball | 2-4 | No OpenStreetMap tag exists and no website listed |
| 53 | Tenis criollo (Tennis Creole, Tenis con paleta) | 2-4 | No OpenStreetMap tag exists and no website listed |
