# Visual polish: scope and options (2026-10-14)

Status: **proposal, no code changed.** Owner picks one option (or mixes), then PRs of one area each.
Source read as text (`app/index.html`, 748 lines; `app/favicon.svg`); no screenshots. Builds on the 2026-10-13 UX audit (removed, in git history) (readability, UX Option A PRs 1-3, done). This is about warmth and look, not layout or content.

## Goal and hard constraints

Make the app feel friendlier and a bit more polished for first-time players, **without losing any detail that exists today**:

- Keep: confirmation levels and their labels, source/evidence lines, link-outs and "Ways to join and follow", suggest-a-change, OSM fix link, count line, legend, filters, all modes, the "inferred, not confirmed" wording (ADR 0007), the CalNeva headline.
- Front end only (`app/index.html`, `favicon.svg`). No change to `venues.json`, dbt or ingestion. No new third-party fonts or libraries that phone home (privacy: only GoatCounter today). No bookings or payments language (we link out).
- Contrast at least WCAG AA in light and dark; 44px touch targets stay; works at 375px and 320px.

## What it looks like today

- Cool GitHub-style greys and blue: `--bg #fff`, `--panel #f6f8fa`, `--accent #0969da`; dark mode is GitHub dark. Reads as a developer tool, not a sports app.
- The logo C uses a deeper blue `#1F5FA8` and gold `#F2B134`, but the page uses neither; the brand is not in the UI.
- Pin colours: confirmed green `#1a7f37`, public blue `#0969da`, inferred gold `#d4a72c`, other grey; events purple `#8250df`; walls orange `#bc4c00`. Pin colours carry meaning, so any palette change must keep them distinguishable (colour-blind check).
- System font stack, flat panels, text-only mode buttons and chips, no sport icons, plain-text empty states.

## Shared changes (all options)

These are low-risk and ship first regardless of the option picked:

1. **Brand colours in the UI:** use the logo blue for the accent and gold for highlights (selected chip, active mode). Define as `:root` tokens with dark-mode pairs; replace hard-coded colours in `.join`, popups and pins with tokens (also fixes the dark-mode gaps noted in the audit).
2. **Sport icons:** small inline SVG set (about 8 families: tennis, pickleball, padel, badminton, squash/racquetball, table tennis, wall/handball, other) beside the sport in list rows, popup "Plays" and the dropdown. Decorative, with the text always kept.
3. **Friendlier copy and states:** warm one-line empty state ("No courts match yet. Try zooming out or clearing a filter" + a Clear button), a loading skeleton for the list, a short welcome line under the headline. Honesty wording is untouched.
4. **Shape and spacing:** 8px spacing scale, 10-12px radius on cards/popups/chips, soft shadow on the popup, consistent 16px gutters.
5. **Motion, light touch:** 150ms hover/press on buttons, popup fade-in; respect `prefers-reduced-motion`.

## Option A: "Fresh court" (recommended; smallest change)

Keep the current layout; restyle and add icons.

```
+-------------------------------+
| (C) CourtConnect CalNeva      |  logo-blue title, gold underline accent
| Find racquet-sport courts     |
| [ Play ][ Watch ][ Walls ]    |  pill buttons, icons, gold when active
| Sport [ Tennis          v ]   |
| [ Search city or venue... ]   |
+-------------------------------+
| 38 venues in view             |
| [icon] Rose Park Courts   [P] |  card rows: sport icon, name,
|        Santa Barbara · 6 ct   |  city, confirmation chip
+-------------------------------+
```

Palette (light / dark): bg `#fbfaf7` warm off-white / `#10151c`; panel `#ffffff` / `#171e27`; accent `#1F5FA8` / `#6aa5ee`; highlight gold `#F2B134` (text on it `#3a2a00`); ok green stays `#1a7f37` / `#3fb950`.
Pros: lowest risk, shippable in 2-3 small PRs, nothing moves, easy to review for lost detail. Cons: still a list + popup; the "wow" is modest.

## Option B: "Court-colour cards" (medium)

Option A plus a richer card/popup treatment.

```
+-------------------------------+
| [photo-less header band:      |  popup top band tinted by status
|  green=confirmed, blue=public,|  (same meaning as pin colour)
|  gold=inferred]               |
| Rose Park Courts              |
| (tennis)(pickle) 6 courts     |  sport icon chips
| Confirmed public · verified   |
| ----------------------------- |
| Plays | Offers | Join         |  popup sections as tabs/accordions,
| Details, sources, corrections |  all content kept, just grouped
+-------------------------------+
```

Adds: tinted status band, grouped popup sections (Plays / Join / Details), a pinned "active filters" chip row with one-tap remove, bigger pin icons (sport glyph inside the circle at zoom 14+).
Pros: biggest friendliness gain on the detail view, which is the heaviest screen. Cons: more JS changes in `venueNode`; sport glyph pins need a sprite and a pin-colour accessibility check; 4-5 PRs.

## Option C: "Playful bold" (largest; not recommended before the beta ends)

Saturated hero header (logo blue gradient with a court-line pattern), large rounded mode tiles with illustrations, custom map style (warmer basemap tones).
Pros: most distinctive. Cons: a custom basemap style is a separate maintenance cost, risks hurting map legibility and pin contrast, and it changes first impressions mid-beta (docs/feedback_round.md findings arrive 10-29..11-01). Mixing results with a redesign would muddy the feedback.

## Recommendation

Ship **A** now (before or alongside the beta follow-ups), then take the popup/card parts of **B** after beta findings, so the feedback decides which details players actually miss. Skip **C** for now.

## Proposed PR sequence (Option A, then B parts)

| PR | Content | Check |
|----|---------|-------|
| 1 | Colour tokens (brand blue/gold, warm neutrals, dark pairs); replace hard-coded colours | AA contrast table in PR; light + dark at 375/320px |
| 2 | Shape/spacing/shadow/motion; pill mode buttons and chips | touch targets still 44px; no wrap in header (see 2026-10-14g) |
| 3 | Sport icon set in list, popup, dropdown | text kept next to every icon; no layout shift |
| 4 | Friendlier empty/loading states and welcome line | honesty labels unchanged |
| 5 (B) | Popup grouping and status band; active-filter chips | diff the popup text before/after: every line still present |
| 6 (B) | Sport glyph pins at high zoom | pin colours still distinguishable (colour-blind simulation) |

**No-detail-lost check for every PR:** list the text labels and links the popup/list rendered before and after for 3 sample venues (confirmed, inferred, NV with link-outs) and paste the diff in the PR. After merge `pages.yml` deploys by itself; hard-refresh (Pages caches up to 10 min).

## Open questions for the owner

1. Option A, A then parts of B, or something else?
2. Is the logo blue + gold the brand to build on, or open to a new accent?
3. Icons: simple monoline (recommended) or filled/colourful?
4. Any detail on today's screens you feel is already too much and could go behind a disclosure (never deleted)?
