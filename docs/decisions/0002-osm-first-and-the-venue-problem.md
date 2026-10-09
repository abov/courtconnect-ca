# ADR 0002: OpenStreetMap as the first court source, and the "venue problem"

**Status:** accepted, with a known gap

## Context
We need statewide court coverage with a free, redistributable source. OpenStreetMap (OSM) fits, with tags for sport, surface, lighting, access and fee.

## What the first LA extract showed (3,253 elements)
- **3,002 of 3,020 tennis courts have no name.** OSM maps individual courts, not facilities.
  A player wants "Griffith Park Tennis Center (12 courts)", not 12 unnamed points.
- Public/private `access` is blank on most records (29 of 3,020 tennis courts are confirmed public).
- Only 4 courts carry more than one sport tag, but many pickleball courts are really re-lined tennis courts.

## Decision
Add a `dim_venue` layer: cluster courts into facilities with spatial proximity (+ shared operator / park polygon),
then enrich venue names and hours from a Places API. Report the result honestly in `mart_sport_coverage`.

## Consequences
Entity resolution becomes the central data-engineering problem, and the coverage dashboard tells users how complete the data is rather than overstating it.
