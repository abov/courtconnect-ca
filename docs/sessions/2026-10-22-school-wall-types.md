# 2026-10-22 School handball walls: imagery pass

- Read Esri World Imagery z19 crops of 323 school-playground OSM wall pins (grouped pins viewed at the size of the group). Recorded only clear reads in `transform/seeds/osm_wall_overrides.csv`: 122 pins (211 courts) = 120 pins one-wall (single slab, plain shadow, no side walls), 2 pins three-wall (back wall plus two side walls: Virginia Peterson Elementary, Pat Butler Elementary). The other 201 pins (~514 courts) stay "assumed one-wall": blurry, shaded, partly hidden, or not every court of the group visible.
- Mixed groups are typed per element (the cluster splits by wall type). Pins with 3+ courts were only recorded when every court was visible in the crop.
- Lesson: DuckDB's CSV sniffer fails on a seed whose quoted evidence contains a semicolon; keep evidence free of `;`.
- Next: a person confirming one-wall vs three-wall on the ground or from a public page beats further imagery reading; the remaining pins are low value.
