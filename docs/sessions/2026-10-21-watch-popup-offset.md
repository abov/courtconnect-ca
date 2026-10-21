# 2026-10-21: Watch and wall popups fit the phone map

Event and wall popups opened from the list now fly with the same offset as venue and social popups (`popupRoom()` helper in `app/index.html`). Checked at 375 px: event and wall popups sit inside the 341 px map, no console errors. Pin clicks (no fly) are unchanged for all four.
Next: nothing; `.claude/launch.json` hardcodes port 8765, so a second preview fails when another session holds it.
