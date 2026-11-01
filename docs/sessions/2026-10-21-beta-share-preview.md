# 2026-10-21: share preview + ref tracking for the beta

Added canonical link, Open Graph / Twitter card tags and `app/share-card.png` (1200x630, made by `ingestion/oneoff/make_share_card.py`) so shared links show a preview; description no longer says Nevada is "coming soon". `?ref=<source>[-tag]` (allowlist in `REF_RE`: reddit, fb, ig, wa, x, nd, hn, tt, nl, sms, friend) logs a GoatCounter event `ref/<value>`; GoatCounter also reads `?ref=` as the referrer natively.
Next: re-run `pages.yml` after merge; check the preview with a link debugger (Facebook Sharing Debugger, opengraph.xyz) and that `ref/` events show up in GoatCounter. At the repo rename, update the three Pages URLs in `app/index.html` (canonical, og:url, og:image/twitter:image).
