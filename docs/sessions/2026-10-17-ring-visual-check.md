# 2026-10-17 visual check of the opening-soon rings (375 px, dark)

Looked at the live page through the browser pane (`preview_start courtconnect-map`), at desktop and 375 px, light and dark. Dark mode only restyles the side panel and popup; the basemap stays light.
- **Solid ring** (confirmed, e.g. Reno Padel Center): clear on the map.
- **Light "reported" ring** was too faint (grey at 65% opacity, thin). Now an opaque dark-grey ring (#57606a, same 3 px weight as the solid ring) and an opaque legend dot, so colour (grey vs green) carries the difference.
- **Existing dark-mode bug found and fixed:** plain popup links (Directions, Website) used the browser's default blue, unreadable on the dark popup; they now use the theme accent.
- **Not changed:** the legend is hidden below 800 px wide, so on phones the rings are explained only by the popup caveat; the popup is tall and scrolls inside the 341 px phone map. Worth a look in the December UX pass.
- Tooling notes: screenshots right after a reload are blank until a second capture; after editing `app/index.html` load with `?v=N` or the browser serves the cached page.

# Guard-rail test (same day)
`transform/tests/assert_padel_has_supporting_signal.sql`: a Padel venue needs evidence rung 1 (club / official page) or 2 (owner or community report); an OSM tag, Overture category or name word alone fails the build. Negative-tested: with Padel San Diego's support removed it failed on exactly that venue. Padel San Diego is now an owner report (it exists; no page found), so it passes honestly. Los Angeles Padel Club: owner says it exists but is strictly members only, so it is `members` and no longer "Opening soon".
