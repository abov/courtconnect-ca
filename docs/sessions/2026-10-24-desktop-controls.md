# 2026-10-24 Desktop controls compaction

At 1280x800 the venue list started at y=632 (about one row visible). `app/index.html`: the Map key no longer reopens on every load (it showed whenever wall pins were on; now once per browser, `cc.keySeen`, about 145 px), and on short desktop screens the headline line and the Sport / Search labels are hidden (labels stay for screen readers), with tighter spacing. Placeholder is now "Search name, city or ZIP (e.g. 90266)".
Prototype on the live page: -68 px from the CSS alone, about -213 px with the key. Check the live site after deploy at 1280x800, 375 px, and with a first-visit (cleared storage) load.
