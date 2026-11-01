# 2026-10-27 Sports sheet cleanup and sync

- Sheet fixes (Real Tennis alt name, typos, trailing spaces, 17 new blurbs, Teqis/Teqpong blurbs) written to the Google Sheet, then synced: 82 sports (new: Padel Pingpong, search term added, count bumped in `sync_sports_sheet.py` and `dbt_project.yml`). The sync also pulled in earlier sheet edits not yet in the seed. Full-refresh build green, `venues.json` re-exported.
- Real Tennis, lawn tennis, 96x32 ft: no CA/NV venue found (0 in the data); not on the map.
- Next: "81 sports" in README, `docs/product_brief.md` and `docs/sport_name_review.md` is stale (`make report` refreshes the coverage snapshot); learn/rules URLs for the 17 new blurbs are still blank.
