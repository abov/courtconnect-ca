# 2026-10-19 Soft Tennis on grass/turf tennis courts

`sport_also_played.csv` gets an optional `only_surfaces` column (e.g. `grass;turf`); Tennis -> Soft Tennis uses it (owner 2026-10-19: soft tennis needs lawn/grass, maybe turf, not hard or clay). Courts with another or unknown surface, Overture places (no surface data) and manual venues without a listed grass/turf surface do not pass it on; the OSM `soft_tennis` tag still counts as before. Result: 19 Soft Tennis venues.
Next: most OSM tennis courts have an unknown surface (21.5k of 23k), so Soft Tennis stays sparse until surfaces are tagged; the same column can restrict other also-played rows.
