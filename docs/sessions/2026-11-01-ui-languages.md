# 2026-11-01: UI languages (ADR 0027)

- `app/index.html` now has `t()` / `tn()`, a footer language picker and `?lang=`; `app/i18n/strings.json` holds 367 machine-drafted rows (es, pt-BR, fr, it, de); `ci/check_i18n.py` is in CI. Checked in the preview in all five languages (no console errors, English unchanged).
- Still English: sport names, venue notes, long explanations, wall sentences, the other three pages. Not checked by a native speaker.
- Next: look at GoatCounter `lang/*` after the beta; then `/es/` pages for search, sport blurbs, native review of Spanish first.
