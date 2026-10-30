# 2026-10-30 Sport level tiers (inferred)
- Added `competitive_tier` to `dim_sport` (inferred from the sheet's popularity_class, competing, org): established 9 (World Official + competing), organized 36 (competing + named governing body, not "?"/defunct), casual 37. Exported as `sports[].t` (1/2/3); the map has Established / Organized / Casual chips above the sport list and a "Level (inferred)" line in the sport card.
- The sheet's Competing column is "Competitive" for 72 of 83 sports, so it only separates organized from casual together with org. No venue or event data is used; beta question: does the split match how people see these sports?
- Next: ask in the beta (docs/feedback_round.md); a stricter "pro tour" tier needs a sourced column in the sheet.
