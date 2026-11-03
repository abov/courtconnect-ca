# 0033. Arizona joins the map

Date: 2026-11-03. Status: accepted, in progress (owner 2026-11-03 asked for it "with the same work as the other states"). Extends ADR 0028 (five-state scope); its per-state step, the "new states get full CA parity" rule and the events/groups pass apply unchanged.

## Context
ADR 0028 step 0 made a new state mostly configuration. Arizona is one landmass and borders CA and NV, so it needs no special handling. OSM relation 162018 was checked against Overpass on 2026-11-03 (Arizona, `ISO3166-2` US-AZ, bounds 31.33 / -114.82 / 37.00 / -109.05, matching the box). Census FIPS is 04; ZIPs run 85xxx-86xxx.

## Decision
- Add `AZ` to `ingestion/regions.json` and the dbt `regions` var; CI test points cover Phoenix, Tucson, Flagstaff, Page, Lake Havasu City, Yuma and Nogales, plus Mesquite NV and Needles CA across the Colorado River, and Nogales, Sonora and Utah/New Mexico as "none".
- The map's home view widens east to the Arizona line (`HOME_BOUNDS`); the region sentence now names Arizona.
- Order: data layer first (this step), then the research passes in ADR 0028's "Per-state step". Expect roughly 1,300-1,900 pins by the ADR's pins-per-million ratio, likely the high end (pickleball, 55+ communities).

## Open for the owner
Scottsdale and Phoenix resorts (closed as in Nevada, or ask-first as in Hawaii); Luke AFB and Davis-Monthan (military rule); research order against Hawaii's remaining rec-center/chain/campus passes.
