# ML plan (after the beta)

Three steps, cheapest first. Each one only **suggests**; a person confirms before anything reaches the map (honesty rule). Start after beta findings (from 2026-11-02).

## Phase 1: review-queue ranker (quick win, ~1 session)
- Labels: confirm/reject rows in `transform/seeds/place_sport_overrides.csv`.
- Clues: words in the name, Overture category, nearby OSM tags, distance to the nearest OSM court, website domain, rules_v2 confidence.
- Small scikit-learn model -> `review_priority` for `mart_sport_evidence.needs_review`. Clear-cut cases first; never auto-confirms.
- **Built 2026-10-14** (started before the beta): `ingestion/rank_review_queue.py`, `make rank-review`, needs `pip install -r requirements-ml.txt`. Writes `docs/review_priority.csv` with `review_priority`, `model_guess` (likely_confirm / likely_reject / unclear), `p_confirm`, and the top three `reasons`. It prints a leave-one-out check, where each label is guessed by a model that never saw it.
- Use: in a review session, start at `review_priority` 1. Check the venue's own page as usual and write the verdict in `place_sport_overrides.csv` (with `evidence`, `verified_on`). Re-run after each batch: new labels retrain it.
- First run (61 labels: 37 confirm, 24 reject; queue 233): leave-one-out accuracy 82%, AUC 0.88; when it says "likely" it was right 85% (47 of 61). Queue split: likely_confirm 104, unclear 116, likely_reject 13. The top ~40 rows (club or association names whose website contains the sport, e.g. table tennis and pickleball clubs) are good first picks. The reject side is weak: most rejects so far are "X Beach Tennis" place names, so it has also learned odd rules ("OSM court within 100 m" counts against). Shop and apparel names are its reliable reject clue. More rejects from other sports will fix this; treat `likely_reject` as "check first", not "probably wrong".
- Rules: the guess never goes into dbt, the export or the map. The rules_v2 confidence score is left out on purpose, because human overrides already feed it (that would leak the answer).

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
