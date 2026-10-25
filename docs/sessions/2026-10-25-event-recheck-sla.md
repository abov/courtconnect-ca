# 2026-10-25 Event re-check SLA

The refresh PR kept failing the scorecard gate: "oldest upcoming-event check" was 15-16 days (limit 14) because 4 PPA rows and the BNP Paribas Open were read by the tournament runs but never re-dated. Re-read ppatour.com/events and bnpparibasopen.com (all five dates unchanged), bumped `verified_on` to 2026-10-25, re-exported.
`docs/tournament_run_parts.md` now tells every part to set `verified_on` on existing upcoming rows it re-confirms. Next: re-run Part 5 (`courtconnect-data-refresh`) after this merges.
