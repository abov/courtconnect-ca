# 2026-10-27: link hitting walls to venues (option A)

- New `int_wall_venue_link` (name match within 300 m, else nearest venue within 150 m; 123 of 448 wall pins link to 118 venues; 25 of the 37 named walls link, the other 12 have no listed venue) with unique/relationships tests. Export adds `wl` on those venues; the popup says "Hitting walls on site: 1 one-wall (reported, not verified)", tagged/inferred labelled "not checked"/"inferred". Walls are not courts: `p`, venue and sport counts unchanged (verified by diffing the export).
- Next: option B (walls become venues) waits for the beta, `docs/walls_into_venues_plan.md`. Re-check the 150 m radius by hand after OSM refreshes (a few distance links are to the nearest park or school, not the exact court).
