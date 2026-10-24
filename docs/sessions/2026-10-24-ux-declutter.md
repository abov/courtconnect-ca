# 2026-10-24 UX declutter (first screen)

Owner found the first screen busy. `app/index.html`: the welcome line shows on the first visit only (`cc.welcomed`; About keeps the text); the Shortlist chip row appears only once something is saved; "Focus mode" moved from the header to the list bar links; the "Clear filters" row is gone (the active-filter chips remove one filter or "Clear all"; `#reset` stays as a hidden script hook).
Checked on the live site at 375 px after #384: Focus mode in the list bar squeezed the count to 143 px (129 px tall), so it went back to the header chips; the Shortlist chip alone hides while empty. Next: the sport-info notes, list bar "more" menu and footer merge from the same list, if still too busy after the beta.
