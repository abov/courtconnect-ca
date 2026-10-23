# 2026-10-23 GoatCounter analysis

- Added events (detail in the path): link-out domain/kind/sport, sport pick, empty results, search misses, mode, filters. `make usage` (`extract_goatcounter.py` + `goat_report.py`) prints the ADR 0013 metrics and sport demand vs `mart_sport_gaps`. Docs: `docs/goat_analysis.md`.
- Tested in the preview with `track` stubbed and on fake CSV data; the real API export is untested (needs the owner's `GOATCOUNTER_API_TOKEN`).
- Next: create the token, exclude own IP, and after a week of real traffic check whether `event/linkout` keeps one title per row (see "Check once" in the doc).
