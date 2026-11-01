# 2026-10-23 UX fixes from the verify pass (PR #373 findings)

`app/index.html` only: 44 px touch targets at a coarse pointer (tools and Near me chips, link buttons, Map key / Hide list side by side at 320, popup links, Share / Save, summaries, popup close, map zoom buttons); glyph layer now starts at zoom 15.5 and grows to 1.0 at 17; new `pts-status` layer adds a tick (name confirmed) or "?" (name guessed) badge from zoom 15.5, so status is not colour-only; map key line added.
Checked at 320 px: no control under 44 px (page and longest popup), no horizontal scroll, badge layer renders. Next: owner eyeballs the badge size on a phone.

Follow-up: cluster circles were the same blue as the "listed business" pin; now dark slate `#24292f` (white count 14.6:1; at least 42 delta-E from every pin colour under protan/deutan/tritan). The new badges pass: tick ring 5.1:1, "?" 6.5:1 on their white disc, and the two differ in shape, so colour-blindness does not matter for them.
