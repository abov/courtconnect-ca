# 2026-11-01: other languages via the browser's own translate

- Owner chose browser translate over a built-in dictionary (`?lang=` / `/es/`). `app/index.html` is `lang="en"` with no `notranslate`, so Chrome, Edge, Safari and Firefox offer to translate it. Place, event, group and wall names and the brand are marked `translate="no"`; the About card has an "Other languages" note.
- Not built, on purpose: `app/i18n/*.json`, a language picker, `/es/` pages. Revisit after the beta if GoatCounter's browser-language counts show real non-English use; then Spanish first (UI strings, the report form), others only on demand. Machine-drafted text must be labelled as such.
- Not verified: how Chrome/Safari translate the live popups (cannot run their translate in the preview). Check on a phone before promoting it.
