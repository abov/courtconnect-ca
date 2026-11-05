# Mexico metro trial: how good is the automatic OSM + Overture layer? (2026-11-05)

ADR 0034 Phase 4 trial, six border-pilot metros only (owner approval 2026-11-05). Fresh per-metro OSM extracts (`extract_osm_courts.py --area <metro>`) and one Overture 2026-10-21.0 places scan over the six metro boxes, both written to a scratch folder (nothing in `data/raw`, seeds or the build). No nationwide run was made. Pin counts come from the current `venues.json` (MX region, 96 pins).

**Surprise first:** the border metros' automatic rows are already on the live map. Of 96 MX pins, 29 are the hand-verified padel clubs (#565/#573/#577); the other **67 are automatic and unverified**, 28 of them with no name at all.

## Counts per metro (Tecate is counted with Tijuana)

| Metro | OSM courts (fresh extract) | named / website / phone / street (OSM tags) | Overture places kept | named / real website / phone | Pins now: verified padel + automatic | Automatic pins: named, by main sport |
|---|---|---|---|---|---|---|
| Tijuana | 77 | 3 / 1 / 1 / 1 | 15 | 15 / 2 / 14 | 5 + 29 | 20 named: 20 tennis (some multi), 5 racquetball, 3 table tennis, 2 pickleball, 1 badminton |
| Mexicali | 50 | 1 / 0 / 0 / 0 | 13 | 13 / 6 / 9 | 12 + 11 | 7 named: 10 tennis, 1 table tennis |
| Ensenada | 29 | 0 / 0 / 0 / 0 | 9 | 9 / 2 / 8 | 3 + 14 | 8 named: 12 tennis, 2 table tennis |
| Hermosillo | 35 | 0 / 0 / 0 / 0 | 16 | 16 / 6 / 13 | 6 + 11 | 7 named: 10 tennis, 1 pickleball |
| Nogales, Son. | 2 | 0 / 0 / 0 / 0 | 0 | none | 0 + 1 | 0 named (1 tennis) |
| San Luis Río Colorado | 0 (8 elements, all US side) | none | 4 | 4 / 1 / 4 | 3 + 1 | 1 named ("Tennis 2 x $500") |
| **Total** | **193** | **4 / 1 / 1 / 1** | **57** | **57 / 17 / 48** | **29 + 67** | **43 named, 24 unnamed**; sports per row count a pin once per sport |

- Only 2% of OSM courts carry a name and one tag in a hundred a street, so almost all names, phones and websites come from Overture (Meta source). Overture "websites" that are Google Maps links were not counted (Google data is not used); two of the 17 counted are a bit.ly menu link or a Linktree page, not a venue site.
- Overture's 57 are mostly padel clubs (about 30, sport_league category), already covered by the verified pins; Playtomic and club pages confirm them well. The rest is the thin part.
- Already pinned: effectively all of it (96 pins vs 193 OSM + 57 Overture rows; the pipeline clusters courts into venues). The trial finds almost nothing new to add; it measures what is already there.

## Measured precision (public-page spot check)

Method: for the named automatic candidates, one public-page lookup each (the venue's own site, Playtomic, local news, public Facebook title; no logins; Pickleheads and Google data not used). 26 candidates were checked: Tijuana 11, Hermosillo 5, Ensenada 6, Mexicali 3, San Luis Río Colorado 1, Nogales 0. That is fewer than 10-15 in the small metros because there are no more named candidates there.

| Result | n | Examples |
|---|---|---|
| **Verified**: a public page shows the venue and its racket facility exist now | 5 (19%) | Club Britania (own site, 2026 Copa Britania), Club Campestre de Tijuana (Zeta Tijuana, 2026 tennis tournament), Estero Beach Resort (own site: 4 outdoor tennis courts), Centro Tenístico de Ensenada (Baja Open House, June 2025), Academia de Tenis Casino de Mexicali (Playtomic lists tennis; same place as the verified Casino pin, so a duplicate) |
| **False match** | 4 (15%) | Novofut (own site: soccer 5 and 7 only, tagged pickleball), Raquetas y Encordados Gracia (a stringing shop, tagged racquetball), Fraccionamiento Chapultepec (a housing subdivision, tagged racquetball), "Tennis 2 x $500" (a price promo, Overture confidence 0.23) |
| **Unverified**: page exists or nothing found | 17 (65%) | Tijuana Tennis Center, Olympo Spa Racquetball, Play Tennis Academia (Facebook title only, no courts or dates); Real del Mar Golf Resort (booking sites only, no own page); JCTennis (USTA page, last news 2023); Baja Racquetball, Xtreme Racquetball, Ping Pong Fit, Escuela de tenis Amparano, Tenis de Mesa Ensenada and Club tenis de mesa Mexicali (nothing found) |

Reading it: **precision of "real, current, racket facility" is about 1 in 5 for the named automatic layer**, with a 95% interval of roughly 8-38% at n=26. "Unverified" is not "does not exist": the search tool is US-focused and Facebook returns only a page title, so recall of a human with Maps and phone calls is higher. Without that, the automatic layer cannot be told apart from noise. The 24 unnamed OSM court pins were not sampled; with no name nothing can be looked up, so they fail the gate by definition.

Other defects seen in the 67: two pins named "Tenis de Mesa Ensenada" (same Overture place twice, confidence 0.07), 24 unnamed pins, several pins named for a university, school or neighbourhood rather than the court, and golf clubs (Los Lagos, Real del Mar) whose tennis is unproven or guests-only (resort rule: ask the owner).

## Proposed gate (tested, refined)

The first draft, "name and (website or an opened page)", is too loose: Novofut has a name and a website, and the site shows soccer. A website field is not evidence. Refined gate, all must hold:
1. a real venue name (not a bare "Cancha de tenis", a neighbourhood, a shop or a price);
2. a public page someone actually opened that names the racket sport and the place, and is dated or current within about 12 months (the club's own site, Playtomic or PlayByPoint club page, a dated news item, a public social post);
3. the point sits in the right city, and the pin takes no US address or city;
4. anything else stays a lead in `venue_leads.csv` or a raw row, not a pin.

Applied to the sample, 5 of 26 pass (19%). Applied to all 67 automatic pins, the gate would hide the 24 unnamed ones and every named pin without an opened page; an estimated 10-15 would stay (the verified ones above plus a few a human would confirm), next to the 29 verified padel clubs.

## What a nationwide run would cost and yield

- Machine time is small: OSM tiles for the country about 30-45 min (ADR estimate; the six metro extracts took a few minutes in total), one Overture scan a couple of minutes. The cost is verification, not extraction.
- Yield: the six metros hold about 5.3 million people and gave 67 automatic pins (about 13 per million). Scaled to about 130 million, expect **1,500-2,500 automatic candidates**, of which the gate would pass about 20%: **300-500 pins**, plus padel clubs found through Playtomic. Large metros (CDMX, Monterrey, Guadalajara) probably have more OSM names than the border, so treat this as a floor for named venues.
- Verification at one lookup per candidate is 1,500-2,500 lookups; by hand that is not feasible, and an automatic verifier (fetch the candidate's website or Playtomic page and check for a racket-sport word) would pass only candidates that already have a website, about 30% of Overture rows.

## Recommendation: no-go on a nationwide pin run

- **No** to loading nationwide OSM + Overture rows as pins. At about 1 in 5 precision, a nationwide layer would put roughly 4 wrong or unprovable pins on the map for each real one, against the owner's "only verifiable" rule.
- **Do first:** apply the gate to MX in the build (hide pins that are not hand-verified, keep them as raw rows or leads) so the 67 automatic border pins stop showing. That is a separate dbt change; it is the same gate the nationwide run would need. Until it ships, the live map breaks the owner's rule in the six border metros.
- **Go instead** with metro-by-metro, demand-gated work (ADR 0034 Phase 3): the padel route works (29 of 29 clubs verified from Playtomic), so extend it with Playtomic/PlayByPoint public club pages, plus federation and club-site lists for tennis, racquetball and table tennis. The automatic layer is useful only as a lead generator, not as pins.
- The extract can still run nationwide later for leads only, once a gate exists, at 30-45 minutes.

## Verified, not newly pinned

No new pins in this PR (`mx-verified-venues` is adding Mexico venues in parallel; avoids duplicates and `venues.json` conflicts). Four checked venues are already on the map as automatic pins and could be promoted to verified through that session: Club Britania (tennisbritania.com; Av. Club Britania 5460, Lomas de Agua Caliente; racquetball per a 2020 Zeta Tijuana story), Club Campestre de Tijuana (Zeta Tijuana, 2026), Estero Beach Resort (esterobeach.com, 4 courts; resort access rule applies) and Centro Tenístico de Ensenada (Baja Open House, June 2025, 2 tennis courts converted to 8 pickleball). Estero Beach and Real del Mar are resorts: ask the owner before pinning.

**Update 2026-11-05:** Club Britania (official, club site), Club Campestre de Tijuana and Centro Tenístico de Ensenada (both reported, news only) were promoted to `manual_venues.csv` and merged into their OSM pins. No pickleball or racquetball was added (event-only and 2018/2020 claims). Estero Beach and Real del Mar still wait for the owner.

**Update 2026-11-05 (third pass):** the unverified named pins were searched again; none could be promoted from a public page (the one pickleball club found, Central Pickleball Club, is on Pickleheads only). Two new verified venues came from federation and press pages instead: CAR Tijuana (table tennis) and the Centro Tenistico de Rosarito (tennis). The 67 automatic pins stay on the map.
