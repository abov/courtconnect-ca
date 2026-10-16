# ML plan (after the beta)

Three steps, cheapest first. Each one only **suggests**; a person confirms before anything reaches the map (honesty rule). Start after beta findings (from 2026-11-02).

## Phase 1: review-queue ranker (quick win, ~1 session)
- Labels: confirm/reject rows in `transform/seeds/place_sport_overrides.csv`.
- Clues: words in the name, Overture category, nearby OSM tags, distance to the nearest OSM court, website domain, rules_v2 confidence.
- Small scikit-learn model -> `review_priority` for `mart_sport_evidence.needs_review`. Clear-cut cases first; never auto-confirms.
- **Built 2026-10-14** (started before the beta): `ingestion/rank_review_queue.py`, `make rank-review`, needs `pip install -r requirements-ml.txt`. Writes `docs/review_priority.csv` with `review_priority`, `model_guess` (likely_confirm / likely_reject / unclear), `p_confirm`, and the top three `reasons`. It prints a leave-one-out check, where each label is guessed by a model that never saw it.
- Use: in a review session, start at `review_priority` 1. Check the venue's own page as usual and write the verdict in `place_sport_overrides.csv` (with `evidence`, `verified_on`). Re-run after each batch: new labels retrain it.
- First run (61 labels: 37 confirm, 24 reject; queue 233): leave-one-out accuracy 82%, AUC 0.88; when it says "likely" it was right 85% (47 of 61). Queue split: likely_confirm 104, unclear 116, likely_reject 13. The top ~40 rows (club or association names whose website contains the sport, e.g. table tennis and pickleball clubs) are good first picks. The reject side is weak: most rejects so far are "X Beach Tennis" place names, so it has also learned odd rules ("OSM court within 100 m" counts against). Shop and apparel names are its reliable reject clue. More rejects from other sports will fix this; treat `likely_reject` as "check first", not "probably wrong".
- Batch 3 (2026-10-15, top 25 + 10 weak-side rows): 18 confirms + 4 rejects from public pages, 13 unclear (dead, blank or hijacked sites, or pages that don't settle it). Now 83 labels (55/28), queue 212: leave-one-out accuracy 86%, AUC 0.93, 'likely' calls right 93%. The top 25 were 17 of 17 right where a page settled it, and 4 of the 5 settled weak-side rows were rejects. New skew: every Tennis label so far is a reject, so 'sport=Tennis' now counts against (Tennis is 25 of the 41 likely_reject rows, e.g. Rancho Bernardo Swim & Tennis Club). Next batch: confirm some real tennis venues first.
- Batch 4 (2026-10-15, tennis skew fix): 7 Tennis confirms from clubs' own pages (Nellie Gail Ranch, Deep Canyon, Peninsula TC, Cambria TC, South Bay TC, Darling TC, Toluca Lake), 5 unclear. Now 90 labels (62/28), queue 205: Tennis likely_reject 25 -> 4 (likely_reject overall 41 -> 21, now mostly Basque Pelota 9 and Pop Tennis 7). Leave-one-out unchanged at 86% / AUC 0.93.
- Batch 5 (2026-10-15, Basque Pelota / Pop Tennis likely_reject, 16 rows): all but one are OSM-only (no place_id), so verdicts went to `osm_court_sport_overrides.csv` (rejects: Nunez Park pelota = outdoor racquetball per the city; Lair of the Golden Bear paddle_tennis = pickleball per the camp page) and `manual_venues.csv` (confirms: Kern County Basque Club fronton, Laguna Woods Village Paddle Tennis Club, 7 courts). Queue 205 -> 201. Labels stay 90: the ranker learns only from `place_sport_overrides`, so OSM-only verdicts don't train it. 12 rows left for the owner (schools' pelota tags, separate paddle_tennis polygons at parks/schools, Chino and South SF Basque courts).
- Rules: the guess never goes into dbt, the export or the map. The rules_v2 confidence score is left out on purpose, because human overrides already feed it (that would leak the answer).

## Addresses for pins without one (not ML; do before phase 2)
On 2026-10-15 about 90% of venues had no street address (CA 9,010 of 9,991; NV 471 of 533), mostly OSM park and school courts. The owner asked for an address on every court.
- This is a lookup, not a model: take the nearest **Overture addresses** point (open data, same release we already load; no API calls) or reverse-geocode with Nominatim (OSM; 1 request a second, so ~3 hours for both states, cache the results). Never Google (ADR 0005).
- Show it as "Nearest address (inferred)", with the distance; skip it when the nearest address is more than ~150 m away, since park courts can sit far from the park's street address.
- Directions don't need it: the popup's Google Maps / Apple Maps links already go to the pin's coordinates.
- Where ML helps: phase 2 can read a park's own page for its street address (with a quote), which beats the nearest-point guess.

## Missing courts at known parks (owner report, 2026-10-15)
Manhattan Heights Park (Manhattan Beach) has at least 2 pickleball and 2 tennis courts; OSM tags only the 2 tennis courts, so pickleball was missing until the owner reported it (`manual_venues.csv`). A fresh `make extract` would not fix this: the data is not in OSM or Overture. Likely many parks look like this (pickleball lines painted on tennis courts, never tagged).
- Phase 2 (city park pages, `docs/public_facility_scan.md`) and phase 3 (aerial photos) are the routes to these. Pickleball lines on a tennis court are hard to see at NAIP resolution, so pages come first.
- Cheap check meanwhile: a city-by-city list of parks with OSM tennis courts but no pickleball tag, checked against each city's own park page (start with the South Bay cities).

## Phase 2: LLM reads public pages (ADR first)
- Pages: Overture places with a website and no sport yet, `*-access` / club-named leads, city rec directories (`docs/public_facility_scan.md`), chain pages (`docs/gym_chain_scan.md`).
- Public pages only, respect robots.txt, no logins (ADR 0007), no Google Places (ADR 0005).
- The LLM returns fixed fields (sports, court count, indoor/outdoor, access, booking link), each with an exact quote; code drops any field whose quote isn't on the page.
- Output: a staged candidate CSV marked inferred, approved in bulk into seeds. Measure precision against the hand-checked overrides.

## Phase 3: courts in aerial photos (pilot)
Finds courts that are in no dataset and on no web page (unmapped park, school, apartment and HOA courts).
- Imagery: NAIP (USDA, public domain, about 0.6 m per pixel), read through Microsoft Planetary Computer's public STAC (no account needed). A tennis court is about 40x18 pixels; a pickleball court is about 22x10, so it is harder to spot.
- Labels at no cost: existing OSM `leisure=pitch` court shapes (tennis, pickleball, basketball as hard negatives).
- Model: small object detector trained on image tiles; prefer permissively licensed ones (torchvision), since Ultralytics YOLO is AGPL.
- Pilot area: one city (Hawthorne, which matches the public facility pilot) and then one Las Vegas zip code. Report precision and recall against OSM before scaling up.
- New detections (not in OSM) -> candidate list -> owner checks on imagery -> **add to OSM** (ADR 0011 edit link) -> they arrive with the normal extract. CourtConnect stores no new data model, and OSM gets better too.
- Imagery shows a court shape, not sport or access: a candidate is "court here, sport and access unknown" until a page or a person says more. Lines alone can't tell tennis from pickleball, and private yards/homes are never added (same rule as the Pop Tennis importer).

### Hawthorne pilot result (2026-10-16)
`ingestion/aerial_pilot.py` (stages `osm`, `chips`, `train`, `detect`; own venv, see `requirements-ml.txt`). NAIP 2022 at 0.6 m via the public Planetary Computer STAC; torchvision Faster R-CNN with a MobileNetV3 backbone (BSD), CPU only, 8 epochs (~80 min).
- **Training data came from outside Hawthorne.** OSM maps only 9 tennis courts there, too few to train on, so the model learned from 731 chips (256 px) in the surrounding LA basin (2,466 racket-court boxes; basketball and other pitches as hard negatives) and Hawthorne is the untouched test area. OSM pitch polygons are the labels, so OSM drawing errors (one polygon around several courts) are learned too.
- **Results on Hawthorne vs OSM** (9 OSM tennis courts, IoU >= 0.3): score >= 0.5 gave 14 detections, 8 matched OSM (recall 8/9 = 0.89, precision against OSM 0.57); >= 0.3: 17 detections, recall 0.89; >= 0.7: recall 0.44; >= 0.9: nothing matched (the model is under-confident). Chip-level check on 81 held-out training-area chips: 195 hits, 101 false, 81 missed.
- **"Precision against OSM" understates it.** The 6 unmatched detections: 5 are racket-court candidates in no OSM pitch (`docs/aerial_candidates_hawthorne.csv`), 1 overlaps a basketball pitch. I looked at the 5 on the imagery: all are real tennis courts. Four are a multi-court school tennis complex next to a school (probably several courts, one box each, overlapping) and one is a single court inside an apartment/townhouse complex (private-looking; the CSV says do not add it to OSM without a public source). So 2 new sites, not 5.
- **Dimensions are rough.** Boxes are 12-27 m on a side, because the model copies OSM's habit of drawing one box around two or more courts. A single tennis court is 23.8 x 11 m (36 x 18 m with run-off), so treat `long_side_m` / `short_side_m` as the size of the detected box, not of one court.
- **Cannot do:** sport (tennis vs pickleball vs padel looks the same at this resolution), access, or indoor courts. Candidates are "court here, sport and access unknown", `status` inferred, and never go into seeds or `venues.json`.
- **Verdict:** the approach works for tennis-sized outdoor courts, but a pilot of this size (one city, 8 epochs, no tuning) finds about 2 new sites in a city of 9 mapped courts. Cost: ~2 sessions of build time, ~80 min CPU training, ~25 MB imagery. A metro-wide run would need merging of neighbouring boxes into one site per complex, a public/private filter from OSM landuse, and a person checking each site on the imagery before anything goes to OSM. Worth continuing with one Las Vegas zip as planned, but expect single-digit new sites per city, not hundreds.
- Reproduce: `python ingestion/aerial_pilot.py osm && ... chips && ... train && ... detect` (imagery and model cache under `data/aerial/`, git-ignored).
