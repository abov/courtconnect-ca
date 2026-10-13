# 0011. Contributing back to OpenStreetMap (link-out only)

Date: 2026-10-13. Status: accepted (2026-10-13). Builds on ADR 0002 (OSM is our main venue source) and ADR 0005.

## Context
Most venues on the map come from OpenStreetMap (OSM). Fixing a missing sport, website or access tag in OSM improves the map for
everyone, and keeps OSM's open data healthy. We want to make that easy without writing to OSM ourselves.

## Decision
1. The detail panel of OSM-sourced venues (source `o` or `b`) links to the OSM editor centred on the venue
   (`https://www.openstreetmap.org/edit#map=19/{lat}/{lon}`). Link out only: nothing is copied or written for the user.
   Hand-curated and places-only venues get no link, to avoid encouraging copying of non-OSM data into OSM.
2. `docs/contribute_to_osm.md` tells contributors which tags matter and what is known to be missing.
3. Edits are made by humans with their own OSM accounts. Claude and the pipeline never create accounts, log in to OSM or upload edits.

## Rules for contributors
- Add only what you saw on the ground or what the venue's own public page says. Never add our INFERRED data (inferred names,
  guessed locations, also-played sports) to OSM.
- Do not paste Overture or Google data into OSM (ADR 0005); their licences are not compatible with ODbL.
- No bulk imports or automated edits (OSM's import and automated-edits guidelines).
- OSM data is ODbL; the app keeps its attribution.

## Not built now
- Direct links to individual OSM elements: the export carries no OSM ids because a venue clusters several courts.
- A generated "OSM fix list" (`make osm-fixes`): consider later if contributors ask for it.

## Consequences
Cheap and compliant, but a contributor has to find the courts on the OSM map themselves, and we cannot see whether anyone fixed anything until the next extract.
