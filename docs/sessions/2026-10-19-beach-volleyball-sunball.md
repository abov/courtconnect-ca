# 2026-10-19 Pro Sunball at beach / sand volleyball courts

Scanned OSM for sand volleyball courts (`ingestion/extract_osm_beach_volleyball.py`, output `data/raw/osm_beach_volleyball.csv`, not loaded into dbt): 1,527 court elements, about 841 sites in CA + NV (787 / 54). Owner then chose NOT to pin them: Pro Sunball is a play-anywhere sport like Frescoball ("any beach or sand volleyball court", `sport_play_anywhere.csv`; ADR 0020 amended).

Next: if the beta shows people want to find sand courts, build an inferred candidate layer from the scan (new ADR; access/privacy rules are in ADR 0020 decision 3). Real Pro Sunball venues or events go in `manual_venues.csv` with evidence.
