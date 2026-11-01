# The ML pilot I killed on purpose

*Draft, 2026-10-29. Facts come from [`docs/ml_plan.md`](../ml_plan.md) (phases 1 and 3), [the 2026-10-27 session note](../sessions/2026-10-27-naip-downey-norwalk-scan.md) and the candidate files it links.*

CourtConnect's map only knows courts that some dataset or web page knows. I wondered whether a model could find the rest by looking at aerial photos. I built the pilot, measured it in four places, and stopped. This is why that was the right result, and what a smaller model that I kept taught me about the same job.

## The idea and its setup

Photos come from NAIP (US government imagery, about 0.6 m per pixel) through a public catalog, so no account and no cost. Labels were free too: OpenStreetMap already outlines many courts. I trained a small object detector (torchvision Faster R-CNN, permissively licensed; I avoided an AGPL one) on 731 image tiles around Los Angeles with 2,466 court boxes. It ran on a CPU in about 80 minutes. A candidate would only ever mean "a court is here, sport and access unknown"; a person checks it on the imagery and adds it to OSM, never to my data directly.

## Four places, four answers

| Area | What I tested | Recall against OSM |
|---|---|---|
| Hawthorne, CA | 9 mapped tennis courts | 0.89 (8 of 9) |
| Las Vegas, one area in zip 89123 | 57 mapped pitches (33 tennis, 24 pickleball), model unchanged | 0.46 |
| Downey/Norwalk, CA | 40 mapped tennis courts, model unchanged | 0.82 |
| Elk Grove, CA | 34 tennis and 14 pickleball, model unchanged | 0.27; 0.29 after fine-tuning on 738 local tiles |

Recall is only half the story, because the point was *new* courts. Hawthorne produced 5 candidates in no OSM pitch; on the imagery they were all real tennis courts, but four belonged to one school complex, so it was **2 new sites**. Las Vegas gave 4 candidates: about 2 plausible, both private-looking, one a parking lot. Downey/Norwalk gave 12; the three in a park or school were a pool, a duplicate of a venue we already list, and a school court I could not confirm. Elk Grove's two were a roof and a pool. Nothing from any area went to the map.

Pickleball was the clear gap: 0 of 14 in Elk Grove, 1 of 14 after tuning. A pickleball court is about 22 x 10 pixels at this resolution, often painted onto a tennis court, and the lines are hard to see.

## Why I stopped

I applied a stop rule: fewer than 3 confirmed new venues from a rescan means do not scale. The repo records the rule and the result, but not the date I wrote the rule down, so treat it as a rule I applied, not as a pre-registered test. Both rescans fell under it. Tuning did not fix the weak tennis recall either. The cost to continue was real (a person checks each site, and every residential hit raises a privacy question), while the benefit was a handful of sites per city. New courts come faster from city pages and community reports. I marked the work dropped, kept the script and the candidate files, and wrote down what would change my mind: a model that can see pickleball lines.

## The ranker I kept

The same plan had a much smaller model: a scikit-learn ranker that orders my review queue so I read the clearest cases first. It never edits data. With 61 hand labels it scored 82% accuracy (leave-one-out) and AUC 0.88; with 83 labels, 86% and 0.93.

It also taught me the lesson I would put first. At 83 labels every Tennis row I had labeled was a reject, so the model had learned "sport = Tennis means reject": 25 of its 41 `likely_reject` rows were Tennis, including a swim-and-tennis club. The accuracy numbers did not warn me, because the labels shared the skew. I found it by reading the rows. Confirming 7 real tennis clubs from their own pages cut Tennis `likely_reject` from 25 to 4, and the headline metrics did not move at all (86%, AUC 0.93). I also left the existing confidence score out of its inputs, because human overrides already feed that score and it would leak the answer.

## What this does not prove

- **OSM was both the teacher and the test.** Recall against OSM measures agreement with a map that has its own gaps and drawing habits (one outline around several courts), and I used a loose overlap threshold (IoU 0.3).
- **The samples are small and unequal.** Nine courts in Hawthorne is not enough to put a number on recall, and I did not break Las Vegas recall down by sport, so the cause of 0.46 is a hypothesis (pickleball, or desert surfaces and light).
- **I did not try everything.** I did not fine-tune on Las Vegas, try other imagery, or train a model for pickleball lines. "Not worth scaling at this setting" is the honest claim, not "aerial detection cannot work".
- **The ranker is evaluated on labels it helped me choose.** I read the top of its queue first, so the label set leans toward what it already liked.

## What I would take from this

- **Define "stop" before you build,** and count what the project actually wants (confirmed new venues), not detection scores.
- **Check the unmatched hits by hand.** The "false positives" were mostly real courts; the *new venues* were still few.
- **Aggregate metrics hide label skew.** Read the rows the model is most sure about.
- **Killing a pilot is a result.** The scripts, candidates and numbers stay in the repo, so the decision can be reopened with evidence.
