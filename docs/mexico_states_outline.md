# Mexico by federal entity: outline

Mexico has 32 federal entities: 31 free and sovereign states (estados) and 1 autonomous entity, Mexico City (Ciudad de México, CDMX). This page is the checklist for covering them. Scope, region shape and effort are in [ADR 0034](decisions/0034-mexico-scope.md): one `MX` region, hand-built parity per metro (not per state), automatic OSM + Overture pins everywhere else, English UI. Entities are keyed by ISO 3166-2 code, the value of the `subregion` column.

Pins are counted from `mart_mx_entity_coverage` (2026-11-12 build, 600 Mexican pins): hand = pins from a seed row a person added, auto = OSM or Overture alone, labelled inferred. Status words come from ADR 0034 and `docs/mexico_metro_trial.md`. Each pin's entity is `dim_venue.subregion`, looked up by `python ingestion/subregion_from_boundaries.py` into `transform/seeds/venue_subregion.csv`; rerun it after adding or moving Mexican pins (the warn-level test `assert_mx_pins_have_subregion` lists any pin it missed). Entities with 0 pins have none yet; the nationwide extract has not run.

## Map outline (light lines)

The map draws a light line around each of the 32 entities, under the pins, from `app/data/mx_state_outline.json` (51 KB; Overture divisions `region` polygons, CDLA-Permissive, simplified to about 3 km, islands under about 200 km2 dropped). Each feature has `name` and the ISO code. Rebuild with `python ingestion/build_mx_state_outline.py`; it warns if the count is not 32. The line is lighter than the covered-state lines (`state_outline.json`, which keeps the single country outline for Mexico).

## Outline

| # | ISO | Entity | Type | Pins (hand / auto) | Status (from ADR 0034) |
|---|---|---|---|---|---|
| 1 | MX-AGU | Aguascalientes | State | 1 (1 / 0) | automatic layer only |
| 2 | MX-BCN | Baja California | State | 78 (16 / 62) | border pilot (Tijuana, Mexicali, Ensenada, Tecate); Rosarito pickleball and El Dorado Ranch (San Felipe) added 2026-11-13 |
| 3 | MX-BCS | Baja California Sur | State | 1 (1 / 0) | Los Cabos, East Cape, Todos Santos, La Paz and Loreto boxes extracted 2026-11-13 (101 OSM courts, automatic pins) plus hand pins in La Paz, Los Barriles, Loreto and El Pescadero (counts not refreshed); the north (Santa Rosalia, Guerrero Negro) is not extracted |
| 4 | MX-CAM | Campeche | State | 0 (0 / 0) | automatic layer only |
| 5 | MX-CHP | Chiapas | State | 0 (0 / 0) | automatic layer only |
| 6 | MX-CHH | Chihuahua | State | 8 (8 / 0) | walled sports pass (Chihuahua City, Ciudad Juárez); FitMax pinned |
| 7 | MX-CMX | Ciudad de México | Autonomous entity | 112 (112 / 0) | Phase 3 metro, parts 1-4 done (padel, pickleball, squash, table tennis, frontón) |
| 8 | MX-COA | Coahuila | State | 4 (4 / 0) | walled sports pass (Torreón, Saltillo) |
| 9 | MX-COL | Colima | State | 6 (6 / 0) | walled sports pass (OSM frontones) |
| 10 | MX-DUR | Durango | State | 0 (0 / 0) | automatic layer only |
| 11 | MX-GUA | Guanajuato | State | 3 (3 / 0) | walled sports pass (Irapuato) |
| 12 | MX-GRO | Guerrero | State | 0 (0 / 0) | automatic layer only |
| 13 | MX-HID | Hidalgo | State | 11 (11 / 0) | automatic layer only |
| 14 | MX-JAL | Jalisco | State | 71 (71 / 0) | Phase 3 metro Guadalajara done; Puerto Vallarta, Autlán walled pins |
| 15 | MX-MEX | México (Estado de México) | State | 70 (70 / 0) | CDMX metro suburbs pinned; east and north are leads |
| 16 | MX-MIC | Michoacán | State | 8 (8 / 0) | walled sports pass (Morelia, Moroleón, Zitácuaro) |
| 17 | MX-MOR | Morelos | State | 0 (0 / 0) | automatic layer only |
| 18 | MX-NAY | Nayarit | State | 1 (1 / 0) | lead only (Tepic Centro de Raqueta) |
| 19 | MX-NLE | Nuevo León | State | 118 (31 / 87) | Phase 3 metro Monterrey done, plus automatic layer |
| 20 | MX-OAX | Oaxaca | State | 1 (1 / 0) | walled sports pass (one pin) |
| 21 | MX-PUE | Puebla | State | 2 (2 / 0) | walled sports pass; Club Britania lead |
| 22 | MX-QUE | Querétaro | State | 17 (17 / 0) | Phase 3 metro done |
| 23 | MX-ROO | Quintana Roo | State | 33 (33 / 0) | Phase 3 metro Cancún / Riviera Maya done, resorts pinned |
| 24 | MX-SLP | San Luis Potosí | State | 3 (3 / 0) | walled sports pass (La Loma, Lomas Raquet Club, Club Deportivo Potosino) |
| 25 | MX-SIN | Sinaloa | State | 0 (0 / 0) | automatic layer only |
| 26 | MX-SON | Sonora | State | 27 (11 / 16) | border pilot (Hermosillo, Nogales, San Luis Río Colorado); Navojoa pinned |
| 27 | MX-TAB | Tabasco | State | 1 (1 / 0) | automatic layer only |
| 28 | MX-TAM | Tamaulipas | State | 1 (1 / 0) | walled sports pass (Ciudad Victoria) |
| 29 | MX-TLA | Tlaxcala | State | 2 (2 / 0) | automatic layer only |
| 30 | MX-VER | Veracruz | State | 3 (3 / 0) | walled sports pass (Boca del Río racquetball and squash) |
| 31 | MX-YUC | Yucatán | State | 16 (16 / 0) | Phase 3 metro Mérida done |
| 32 | MX-ZAC | Zacatecas | State | 2 (2 / 0) | walled sports pass (Jerez) |

"Automatic layer only" means no hand work yet. It does not mean no pins: the nationwide automatic extract is deferred (ADR 0034, Phase 4), so such an entity may have none until it runs.

## Per-entity checklist

Run this per entity, only where demand or an owner request says so (ADR 0034; hand parity is per metro):

1. Data layer: OSM courts and Overture places for the entity's metros; Spanish terms and aliases already apply.
2. Pins labelled inferred (one rule for every region, ADR 0034); no inferred street for home-like pins.
3. Padel (Playtomic public club pages), then tennis, pickleball, squash, racquetball, table tennis, frontenis and pelota, from public pages only.
4. Events, leagues and groups: state sports institute and federation pages; record searches in `docs/event_group_search.md`.
5. Leads that cannot be pinned go in `venue_leads.csv`.

## Open items

- The Phase 4 nationwide extract (30-45 min) is what fills the "automatic layer only" rows; it needs the owner's go.
- Demand threshold for starting a hand-built metro beyond the six core ones is not set (ADR 0034, "Still open").
