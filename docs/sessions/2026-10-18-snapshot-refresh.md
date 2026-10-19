# 2026-10-18 Coverage snapshot + quality scorecard refresh
Regenerated `docs/coverage_snapshot.md`, `docs/sport_name_review.md` (`make report`) and `docs/data_quality.md` + trend row (`make quality`) from a fresh DuckDB build (239 dbt nodes pass): snapshot now shows CA 9,710 and NV 547 venues (it still said "Nevada has no data" from 2026-10-14). Scorecard 6/7 met; the one breach is named venues 14.0 % vs the 25 % target (4,483 of 10,257).
Next: pick from "Open, in order" in CLAUDE.md; the named-venue breach is the main quality gap (city/address fill and club-named venues pass 2 move it).
