# 2026-10-23 ADR 0022: watch event format split

Wrote ADR 0022 (proposed). Finding: `watch_format`, its accepted_values test and the labels (`watch_party`, `dome_screening`, `broadcast_only`) already exist; no row uses them. Recommendation: keep the six values, group them as on-site vs screening in the app, add a "not played here" popup line and one test; no new `screening` value.
Next (owner accepts first): the small app + test PR, then Cosm LA rows only from a dated public listing.
CLAUDE.md "Open" line should become: "Watch events, screenings (ADR 0022, done): keep the six `watch_format` values, popup line 'Shown on a screen here; not played at this venue', one test for screening rows; then add Cosm LA rows only when a dated public listing exists."
