# 2026-10-25 search interest (Google Trends)

Built the import: 4 Trends queries read from the public pages' own responses -> seeds `search_interest` + `search_metros` -> `int_search_interest` -> `mart_search_vs_coverage`, `make interest`, test. Venues go to the nearest metro anchor (no Nielsen county list: licensing). First gap candidates: Padel in El Centro (weak), Las Vegas, Palm Springs.
Next: quarterly refresh runs from the scheduled task `courtconnect-search-interest-refresh` (procedure in `docs/search_interest_plan.md`); the owner decides whether to act on the gaps.
