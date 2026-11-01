# 0027. UI languages: English source text, machine-drafted translations, language picker

Date: 2026-11-01. Status: **accepted** (owner asked for it in chat).

## Context
The map is English only. The owner wants Spanish, Brazilian Portuguese, French, Italian and German, with more later. Browser translate alone (PR 459) leaves JS-built popups and fragments to the translator and cannot be linked to in a language.

## Decision
- **English is the source and the key.** `t("Near me")` looks the phrase up in `app/i18n/strings.json` (`{"English": [es, pt-BR, fr, it, de]}`) and falls back to the English, so a missing row never breaks the page. Static HTML text is swapped once at load by exact match; the label tables (`QNAME`, `OFFER`, ...) are swapped once at boot.
- **Which language:** `?lang=` first, then the choice saved by the footer picker (localStorage `cc.lang`), then the browser's language list, else English. Switching reloads the page; filters survive in the `#hash`. A `lang/<code>` event counts the use (fixed vocabulary).
- **Honesty:** the translations are machine-drafted and not reviewed by native speakers; the About card and the picker's tooltip say so. Sport names, venue notes, long explanations and sport blurbs stay English (browser translate still works for them; names are `translate="no"`).
- **Plurals and dates** use the language's own rules (`Intl.PluralRules`, `Intl.DateTimeFormat`), so French says "0 lieu".
- **Guard rail:** `ci/check_i18n.py` (in CI) fails on a row without one text per language, changed `{placeholders}`, a stale key, or a `t("...")` literal with no row.

## Consequences
- Changing an English UI string means updating its row (CI says which).
- Adding a language = add a column to every row, one `LANGS` entry; nothing else.
- Not done: other pages (`how-its-built`, `ask-the-data`, `run-history`), the 63 sport blurbs, `/es/` URLs for search engines (`hreflang`). Revisit with GoatCounter's `lang/*` counts.
