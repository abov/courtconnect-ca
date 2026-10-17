# 2026-10-17 visual check of the opening-soon rings (375 px, dark)

Looked at the live page through the browser pane (`preview_start courtconnect-map`), at desktop and 375 px, light and dark. Dark mode only restyles the side panel and popup; the basemap stays light.
- **Solid ring** (confirmed, e.g. Reno Padel Center): clear on the map.
- **Light "reported" ring** was too faint (grey at 65% opacity, thin). Now an opaque dark-grey ring (#57606a, same 3 px weight as the solid ring) and an opaque legend dot, so colour (grey vs green) carries the difference.
- **Existing dark-mode bug found and fixed:** plain popup links (Directions, Website) used the browser's default blue, unreadable on the dark popup; they now use the theme accent.
- **Not changed:** the legend is hidden below 800 px wide, so on phones the rings are explained only by the popup caveat; the popup is tall and scrolls inside the 341 px phone map. Worth a look in the December UX pass.
- Tooling notes: screenshots right after a reload are blank until a second capture; after editing `app/index.html` load with `?v=N` or the browser serves the cached page.
