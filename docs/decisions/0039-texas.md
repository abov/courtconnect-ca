# 0039. Texas joins the map

Date: 2026-11-12. Status: accepted, in progress (owner 2026-11-12 asked for Texas "with the same work as the other states"). The data layer is built: 5,403 pins on the first build (18,015 OSM court elements, 789 Overture places, 15 padel clubs confirmed from their own or Playtomic pages). Research passes (events, groups, walls by hand, rec centers, chains, campuses, other sports) are open, metro by metro. Extends ADR 0028 (per-state step), ADR 0035 (Arizona, the precedent) and the "new states get full CA parity" rule (`docs/new_region_checklist.md`). The data layer is the first step; the research passes follow metro by metro.

## Context
Texas is one landmass, the largest state we cover (about 31 million people), and shares a 1,254 mile border with Mexico. OSM relation 114690 was checked against Overpass on 2026-11-12 (Texas, `ISO3166-2` US-TX, bounds 25.84 / -106.65 / 36.50 / -93.51, matching the box). Census FIPS is 48; ZIPs run 75xxx-79xxx and 73301 / 88xxx.

## Decision
- Add `TX` to `ingestion/regions.json` and the dbt `regions` var. `region_at` resolves the Mexico overlap by polygon (as for Tijuana / San Ysidro), so El Paso is TX and Ciudad Juárez stays MX, Brownsville is TX and Matamoros is MX; CI test points cover both sides of the Rio Grande at El Paso, Brownsville and Laredo, plus Louisiana and Oklahoma as "none".
- The home view already spans the whole country (`HOME_BOUNDS` reaches -85 and Cancún), so Texas needs no shortcut; the State dropdown gets a Texas box.
- Order: the automatic OSM + Overture layer for the whole state first (labelled inferred, one rule for every region, ADR 0034), then the research passes of the checklist one metro at a time: Houston, Dallas-Fort Worth, Austin, San Antonio, El Paso, Rio Grande Valley, then the rest.
- New Mexico is a separate session and PR; shared files (region sentence, `regions.json`, the dbt var) will need a trivial merge.

## Open for the owner
Resorts and hotels with courts (Hill Country, Galveston, Dallas) follow ADR 0028's all-states resort rule: case by case from the resort's own public page; none added in this step. Military bases (JBSA, Fort Cavazos, Fort Bliss) follow the military rule in ADR 0014.

## Research passes still open (per metro, in order)
Houston pass 1 done 2026-11-12 (Houston city and Woodlands Township pickleball, Life Time, 24 Hour and LA Fitness, padel clubs from Playtomic pages, table tennis, badminton, campus, events, groups; sections in `docs/event_group_search.md`, `public_facility_scan.md`, `padel_scan.md`, `gym_chain_scan.md`). Houston still open: Sugar Land, Pearland, Katy, Missouri City and Harris County precinct park pages, YMCA branches, Rice and HCC, the padel leads (West43, PELOTA, U-Padel Woodlands, Woodlands Padel, WePadel, Punto Azul), Houston Squash Club, hand-found walls (none found), beach and pop tennis. Dallas-Fort Worth, Austin, San Antonio, El Paso, Rio Grande Valley, then Lubbock, Amarillo, Corpus Christi and the rest. Per metro: events and tournaments, leagues and groups, social events, city park and rec pages, YMCA/JCC, campuses, chains, hand-found walls and handball courts, then the minor sports (squash, racquetball, table tennis, badminton, pop tennis, beach tennis). `python ci/region_parity.py --region TX` shows the zeros; none is logged as "searched, empty" yet. Unconfirmed padel clubs are leads in `venue_leads.csv`.

## Austin and San Antonio pass (2026-11-12)
Done in the first depth: five padel clubs, two campus racquetball/handball venues, Escobar Park's handball courts, two dated events, seven open-play series, one Meetup group and booking link-outs (details in the Texas sections of `docs/event_group_search.md`, `public_facility_scan.md`, `padel_scan.md`, `gym_chain_scan.md`). Open: Round Rock, Cedar Park, Georgetown, New Braunfels, San Marcos city pages, Texas State and Trinity, Life Time and YMCA pages, the Austin tennis centers' practice walls, the Searight Park handball wall and San Antonio's 3-wall courts (leads in `venue_leads.csv`).

## Notes from the data layer
- Texas towns share names with covered places (Reno, San Diego, Henderson, Oregon, Wall), so the ask box now picks the state with the most pins for a city name and skips "Wall" as a city.
- `extract_overture_addresses.py --region` could not read the shared address file once it held a quoted street with a comma (the CSV sniffer lost the quote character); it now sets the quote and escape characters.
