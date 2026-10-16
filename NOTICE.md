# Data attribution

This project combines open data. Please keep these notices if you reuse the data.

**OpenStreetMap** (courts, parks, schools, clubs): (c) OpenStreetMap contributors, available under the
[Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/). Data fetched through the Overpass API.

**Overture Maps Foundation** (places): the Overture Maps places dataset, release 2026-09-23.1. Individual records come from several
sources, each carrying its own license in the `license` column of `raw.overture_places`: mostly CDLA-Permissive-2.0, plus Apache-2.0
and CC0-1.0. Its addresses theme (address points near our pins, `raw.overture_addresses`, same release) fills pins that have no street address and is shown on the map as "Nearest address (inferred)". See [overturemaps.org](https://overturemaps.org) and its attribution page for the current terms.

**Not used:** Google Places content is deliberately not stored in this repository or warehouse. See
`docs/decisions/0005-overture-places-and-google-terms.md`.

The code in this repository is separate from this data and is not covered by these data licenses.
