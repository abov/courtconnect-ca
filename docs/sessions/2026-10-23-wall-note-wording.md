# 2026-10-23 Wall note wording

The Play-mode wall note (`app/index.html`, `showWallNote`) said walls come from OpenStreetMap only. 33 of the walls on the map come from `manual_walls.csv` (city pages and owner/community visit reports), so the sentence now says "OpenStreetMap, city pages and visit reports" and "ones nobody has mapped or reported are missing". The counts in the note are computed at runtime and were not stale. Next: re-run `pages.yml` after merge (it is manual only).
