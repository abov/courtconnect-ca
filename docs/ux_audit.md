# UX audit and layout options (2026-10-13)

Source: `app/index.html` (671 lines, one static file, MapLibre). Read as text; no screenshots.

## 1. What users see today

**First load (left panel, 390px, map on the right; on phones the map takes 52vh and the panel is below it)**
1. Title + logo, headline, two text links ("How complete is this data?", "Near me")
2. Three mode buttons: Find a place to play / Watch a match / Hitting walls
3. Sport dropdown (+ "any beach" note), search box
4. Collapsed "More filters" (surface, Public / Private-members / Has website / Hide unnamed, what they offer) and "Clear filters"
5. Count line ("N venues match · M in view · nearest 40 ..."), list of up to 40 venues (name, city + sports, badges)
6. Legend (4 dot colours) and footer attribution

**Venue detail (a map popup, 290px wide, max 55vh, scrolls):**
name, confirmation badge, status badges (reported/confirmed, "public access not confirmed"), address, Plays, facts, Offers, Notes, Website, "Ways to join and follow" (buttons + disclaimer), Suggest a change, OSM fix link, Source (+ inference note).

## 2. Problems that hurt readability

| # | Finding | Where |
|---|---------|-------|
| 1 | Header stacks 5 things (title, headline, 2 links, 3 modes) before any control; the primary choice (sport + where) is third | `header`, `.controls` |
| 2 | The list, not the map, is the main result view, but its header is a long sentence ("nearest 40 to the map centre:") | `#count` |
| 3 | Venue detail is a small popup: ~12 items in a 290px scroll box; important (Plays, Join) and technical (Source, OSM fix) lines have equal weight; on phones it competes with the panel | `venueNode` |
| 4 | Jargon: "Name inferred from park/school", "Business listing", `QSHORT/QNAME` badges, "Public access not confirmed" with no explanation | badges, legend |
| 5 | Legend explains name quality only, not what the pin colours mean for players (public / private / event) | `.legend` |
| 6 | Small text and targets: 11-12.5px badges/labels, chips about 26px tall (below the 44px touch guideline); `.join` and popup colours hard-coded (do not follow dark mode) | CSS |
| 7 | "More filters" summary is a long label; "Clear filters" sits below it, far from the active filters; no active-filter summary | `#moreFilters` |
| 8 | Phone layout: map 52vh on top, panel under it; you cannot see the map and the list together, and detail opens on the map, behind the scroll | `@media` |

Nothing is wrong with the honesty labels; the goal is to keep every one of them and make them quieter, not remove them.

## 3. Content that must survive (checklist)

Modes (play/watch/walls); sport dropdown + any-beach note; search; surface, public, members, website, hide-unnamed chips; offers chips; wall-type chips; Near me; coverage dialog; count + in-view; list rows (name, city, sports, quality badge, join/offers badge); legend; attribution; venue detail fields (name, quality badge, confirmation + date + courts, public-access warning, address, Plays incl. also-played grouping, facts, Offers, Notes, Website, Ways to join and follow + no-payments disclaimer, Suggest a change, OSM link, Source + inference note); URL hash state (`mode, wall, sport, on, offer, q`, old `#access=members`); analytics events.

## 4. Layout options

### A. "Clean panel" (smallest change, lowest risk)
Keep the left panel + popup. Restyle only: CSS tokens (type scale 14/16/12, spacing 8px grid, 44px chips), header reduced to logo + title + one-line headline, modes become a tab bar, "How complete is this data?" and "Near me" move to the footer/search row, active-filter summary and Clear next to it, list rows get a coloured left bar and plain-language badges, popup sections grouped (Plays / Ways to join first; Source, Suggest, OSM under a "Details and sources" disclosure), dark-mode-safe popup colours.
- Pros: 1-2 PRs, no behaviour change, URL state untouched. Cons: popup stays small; phone layout still stacked.

### B. "Search first + detail drawer" (recommended)
Top bar over the map: logo, one search box ("Sport, city or venue"), mode tabs. Filters in a single "Filters" button that opens a sheet with chip groups and a live count ("Show 312 venues"). Results list in a side panel (desktop) or a draggable bottom sheet (phone: peek = 3 rows, half, full). Selecting a venue replaces the popup with a **detail drawer** (same panel slot / bottom sheet) with a header (name, one-line status), then sections: Plays, Ways to join and follow, About (address, website, notes, facts), and a collapsed "Sources and corrections" (confirmation, source, inference note, Suggest a change, OSM fix). Legend becomes a small "Key" button on the map.
- Pros: best readability on phones, room for every field, clearer hierarchy. Cons: biggest rewrite of `index.html` (about 4 PRs), needs careful focus and keyboard handling.

### C. "Map-first minimal"
Full-screen map, floating search + sport pill, results behind a "List (312)" toggle; detail as a bottom card.
- Pros: most visual, simplest first impression. Cons: hides the list and the honesty context by default, hardest to keep every detail visible, weakest for the "easy to read" goal.

## 5. Recommendation

Option **B**, shipped in the staged order (tokens -> top bar and filter sheet -> detail drawer -> mobile bottom sheet) so each PR is reviewable and A's quick wins (tokens, jargon, 44px targets, dark-mode colours) land first. No framework; keep the single static file (or split CSS/JS only if the owner agrees).

## 6. Open questions for the owner
1. Which option (A, B, C)? 2. OK to rename badges (e.g. "Name inferred" -> "Name guessed from park", with a tooltip)? 3. Keep "How complete is this data?" prominent (header) or move to the footer/Key? 4. Split `index.html` into CSS and JS files, or keep one file?
