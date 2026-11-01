# 2026-11-01: built-in UI languages removed

- Reverted #461 and #464 (picker, `?lang=`, `app/i18n/strings.json`, `ci/check_i18n.py`, ADR 0027): Chrome and Safari already translate pages, so the extra layer is not worth maintaining. Kept #459: names are `translate="no"` and the About card has the "Other languages" note.
- If non-English use shows up after the beta (GoatCounter language counts), the tried design is in git history (b22fc06, 6a7aaed): English text as key, machine-drafted rows, 350 strings x 5 languages.
