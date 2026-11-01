{% docs __overview__ %}

# CourtConnect CalNeva: data model

One map of racket-sport venues in California and Nevada, built from open data. This site documents the dbt project: every model, seed and test, and the lineage between them. Use the lineage graph (bottom right) to follow a venue from raw data to the exported map.

**Layers, left to right**

- **Sources and seeds.** Raw OpenStreetMap courts, walls and parent areas; Overture places and addresses; Census boundaries; the master sports sheet. Seeds are human knowledge kept as code: each hand-added fact carries `evidence` and `verified_on`.
- **Staging (`stg_*`).** One model per source or seed: typed, standardised, de-duplicated.
- **Intermediate (`int_*`).** The hard part: a proximity graph of courts, clustering courts into venues, and matching Overture places to those venues (`int_place_venue_match`, scored against a hand-labelled gold set).
- **Core (`dim_*`, `bridge_*`).** Business entities: venues, courts, places, sports, walls.
- **Marts (`mart_*`).** What the export and the reports read, such as `mart_venue_finder` and `mart_sport_coverage`.

The `courtconnect_map` exposure shows which marts feed the live map. Tests guard the logic (clusters converge, every court has one venue, confirmed venues need evidence).

**About this site.** It is built in CI from a small sample dataset (the Pasadena area), so it shows structure, lineage and descriptions but no real venue data. The live numbers are on the [How it's built](../how-its-built.html) page; decisions are in the repository's `docs/decisions`.

{% enddocs %}
