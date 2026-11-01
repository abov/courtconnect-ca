# 2026-10-23 UI/UX small fixes

- "Near me" errors now show in the search note instead of `alert()`; added `manifest.webmanifest`, `icon-180/192/512.png` (apple-touch-icon, add to home screen, no service worker) and theme-color.
- axe-core pass (light + dark, About, Coverage, open popup): found unstyled links at 1.94 contrast in dark and a non-focusable scroll region in the coverage dialog; fixed (`a` colour token, `tabindex=0`), now 0 violations.
- Next: the responsive/dark/colour-blind check of PR 5-6 runs in its own session (`ux-verify`); the rest waits for the beta.
