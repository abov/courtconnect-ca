# 2026-10-17 Gold set slice 2 and facility_name match rule

Gold file 40 -> 90 pairs (3 new strata, one a seeded random sample). New third tier in `int_place_venue_match` (`facility_name`: place named after the court's park/school/centre, or sharing its street address, within 200 m): the 17 first-slice misses fall to 3, no wrong merge on the 90 pairs, 30 places stop being duplicate pins. Details and caveats (selection bias, tennis academies merged by shared address) in `docs/gold_set_plan.md`, "Second slice".
Next: second random sample including places 300 m+ from courts; decide whether academies sharing a school address should stay separate pins.
