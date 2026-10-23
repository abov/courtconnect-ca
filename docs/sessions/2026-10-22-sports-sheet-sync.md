# 2026-10-22 sports sheet sync (Basque split, 81 sports, filled cells)

- Ran `make sync-sports`: `all_racquet.csv` now has the 12 hand-filled url/Rules cells and a few filled Country/Association cells. The eight "Basque Pelota: ..." rows, `EXPECTED_SPORTS` and `expected_racket_sports` were already at 81 from an earlier sync, so no seed rename was needed (`ci/check_sport_names.py` passes; the remaining "Xare"/"Frontenis"/"Jai alai" strings are free-text aliases in `sport_aliases.csv` on purpose). Fixed the stale "expected: 76" comment in `assert_all_racket_sports_loaded.sql` and the README coverage sentence (now 81 sports, 35 covered, 39 nothing found).
- Regenerated `app/data/venues.json` and `docs/coverage_snapshot.md` / `docs/sport_name_review.md`; full dbt build green (280 pass), CI checks pass.
- Next: nothing from this sync. Sport About card blurbs still wait on the owner (roadmap, parked).
