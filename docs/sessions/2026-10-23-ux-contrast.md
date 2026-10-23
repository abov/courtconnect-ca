# 2026-10-23 UX contrast leftovers

`app/index.html`: the pin glyph is dark (#1f2328) on grey as well as gold and rings (white only on green and blue), so grey went from 3.04 to 5.2:1; fills untouched, colour-blind separation unchanged (lowest 20.0, green vs blue under tritan). Glyph size 0.85/1/1.1 at zoom 15.5/16/17 (was 0.7/0.85/1), inside the same pin; light `--warn` #9a6700 -> #855700 lifts the gold chip from 4.66 to 5.99:1 (dark unchanged, 7.26).
axe 4.10.2 light and dark with the inferred popup open: 0 violations after underlining the expanded MapLibre credits links (3 `link-in-text-block` hits, not caused by this change). Checked by computed styles and maths only; glyph rendering was not seen (browser pane hidden, map did not draw), so owner eyeballs the pins at zoom 16.
