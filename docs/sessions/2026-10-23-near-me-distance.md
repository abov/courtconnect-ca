# 2026-10-23 Near me distances

- After a successful "Near me", list rows (venues and hitting walls) lead with "1.2 mi" straight-line from the user, and Watch / Social lists sort nearest-first (`userPos`, `distLabel`, `nearCmp` fallback). The venue list already sorted by distance from the map centre, so only the label and the events order were new. Position stays in the tab, never stored or sent.
- Checked in the preview with a mocked position (Santa Monica: 0.5, 0.6, 0.6, 0.7, 0.9 mi, ascending; no console errors). Not tried on a real phone GPS.
- Next: show the distance in the popup too if the beta asks; PR 376 (cluster colour) also touches `app/index.html`.
