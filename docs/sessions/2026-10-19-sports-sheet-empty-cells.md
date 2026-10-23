# 2026-10-19 Sports sheet: empty cells audit

Pulled the Google Sheet (tab "All Racquet", 77 sports) as CSV and counted blanks per column. Blanks: Alt Sp Name 51, Players 4, Org 43, Yr Origin 5, Active Loc 26, Court Dim 36, Court Surface 11, Base Gear 2, Net Type 40, Net Ht 54, Competing 7, url 48, Rules 67. Many Net/Court blanks are "not applicable", not missing: the sheet has no way to say that yet.

Drafted sourced `url` fills in `docs/sheet_url_fill_draft.csv` (14 url + 2 Rules values, 11 rows with "none found"). 28 of the 48 blank-url sports were searched (the rest, e.g. 360Ball, Biraq, Goodminton, Indiaca Tennis, Knuckle Racket, Miniten Thug, Outdoor Racquetball, Sandball, Speedball, Street Tennis, Taiji Bailong, Wall Pong, were not); most obscure Rec sports have no official site, so the proposed values are mostly reference pages and are marked as such. Nothing was written to the sheet.

Second pass (same day): checked Wikipedia via its API for the empty and unsearched rows. Draft now has 5 official, 13 Wikipedia, 5 other-reference, 2 Rules, 23 none-found rows. Still no official-site search for: Naked Tennis, Biraq, Frescotennis, Indiaca Tennis, Knuckle Racket, Tennis Baseball, Wall Pong, Sandball, Speedball. Owner questions: Miniten "Thug", String Paddleball and Street Tennis may not be the sports Wikipedia describes.

Third pass: dropped the doubtful rows (Miniten Thug, String Paddleball, Street Tennis) from the url draft (45 rows left). Org column (43 blank) drafted in `docs/sheet_org_fill_draft.csv`: 8 proposals (2 high, 3 medium, 3 low), the rest none found or not searched. Yr Origin (5 blank: 3-wall Paddleball, Hand Tennis, Tennis Baseball, Riftball, Wackitball) drafted in `docs/sheet_yr_origin_fill_draft.csv`: only 1 low-confidence proposal (Hand Tennis ~1100, identity of the row unclear); the other 4 have no documented year, so they stay blank. Wackitball is a new row in the sheet since the first pull (77 sports). Active Loc (26 blank) drafted in `docs/sheet_active_loc_fill_draft.csv`: 15 proposals (5 medium, 10 low), 10 rows with none found/skipped, plus a FLAG row: three sheet years (Knuckle Racket, Eclipseball, 360Ball) differ from the only source found. The sheet was re-pulled mid-session and had no changes since the Org pass. Court Dim (36), Net Type (40), Net Ht (54), Rules (67) and Alt Sp Name are not started; many of those are "not applicable", not missing.

Rule set by the owner: `url` = official site; if none exists, a Wikipedia page is the backup; only if there is no Wikipedia page, another reference page (tagged in the `tier` column). Next: the owner picks which proposals to apply; the 20 unsearched blank-url rows and the 11 "none found" rows still need a Wikipedia check; then the next column (Org or Yr Origin).

## Paste-ready files (2026-10-22)

Built from a fresh pull of the sheet (81 sports, rows 2-82). The sheet changed under us: Basque Pelota was split into eight "Basque Pelota: ..." rows (Frontenis and Xare renamed, Jai alai folded in), and some blanks were filled by hand (Soft Tennis url+Org, Shuttleball Rules, 360Ball url, Knuckle Racket and Pitton Active Loc), so those drafts were dropped. Only cells still blank are proposed.

- `docs/sheet_paste_ready_changes.csv`: 19 high/medium cells with their sheet address (F54, P20, ...). The safest route: type or paste each cell.
- `docs/sheet_paste_ready.csv`: Sport, Org, Active Loc, url, Rules for every row, current values kept, 19 cells filled. Row N here is row N in the sheet. Import as a new tab and copy a column back only if nobody edits the sheet meanwhile (a column paste overwrites the whole column).
- `docs/sheet_paste_low_confidence.csv`: 19 low-confidence proposals, not recommended without checking.

Not paste-ready: the three sheet years that disagree with the one source found (Knuckle Racket, Eclipseball, 360Ball). Repo follow-up: the sheet's Basque Pelota rename means seeds, aliases and `EXPECTED_SPORTS` (76) need checking at the next `make sync-sports`.

## Written to the sheet (2026-10-22)

With the Google Sheets connector on, wrote the blank cells only, one cell at a time, matched by Sport name and checked by reading the range back. 12 cells written: url for Australian Racquetball (P20), Downside Ball Game (P30), Paleta frontón (P33), Road Tennis (P34), Jokari (P47), Outdoor Racquetball (P54), Pang Pong (P55), Pitton (P56), Qianball (P58), Taiji Bailong (P72), Totem Tennis (P77); Rules for Smolball (Q65). The other 7 of the 19 high/medium cells (Org and Active Loc for Outdoor Racquetball, Qianball, Taiji Bailong, 360Ball, Shuttleball) had already been filled with the same values by someone else, so nothing was overwritten. The 19 low-confidence proposals and the three year conflicts (Knuckle Racket, Eclipseball, 360Ball) were not written. Next `make sync-sports` will pick these up; check the Basque Pelota rename then.

## Overwrites approved by the owner (2026-10-23)

- P20 Australian Racquetball url: the link written earlier (`squash.org.au/w/participation/Racquetball`) returns 404 (the squash.org.au site appears gone); replaced with `https://www.squashaus.com.au/`. All other 11 written links load.
- Yr Origin: Knuckle Racket G49 2004 -> 2009 and Eclipseball G40 1980 -> 1985, both from the Topend Sports page (single user-submitted source, not independently confirmed). 360Ball (G38, sheet 2011; Topend says created 1990, recreated 2010) left alone until the owner picks a value.
- Still not written: 19 low-confidence proposals in `docs/sheet_paste_low_confidence.csv`. Recommended subset of 7 (Frescoball, Smashball, Table Squash, Toccer urls; Toccer Org; Eclipseball and Racket Hockey urls) awaits a yes. Rapidball's url proposal 404s; drop it.
- Front-end note at `app/index.html:811` says walls come from OpenStreetMap only; 33 of them (`manual_walls.csv`) come from city pages and visit reports. Not edited.
