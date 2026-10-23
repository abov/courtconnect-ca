# 2026-10-23 UX fixes from the verify pass (PR #373 findings)

`app/index.html` only: 44 px touch targets at a coarse pointer (tools and Near me chips, link buttons, Map key / Hide list side by side at 320, popup links, Share / Save, summaries, popup close, map zoom buttons); glyph layer now starts at zoom 15.5 and grows to 1.0 at 17; new `pts-status` layer adds a tick (name confirmed) or "?" (name guessed) badge from zoom 15.5, so status is not colour-only; map key line added.
Checked at 320 px: no control under 44 px (page and longest popup), no horizontal scroll, badge layer renders. Next: owner eyeballs the badge size on a phone.
