# Talk and walkthrough outline

*Written 2026-10-29 for interviews, meetups and a screen-recorded walkthrough. It is an outline, not a finished deck: every number below has a source in brackets, and the recheck list at the end says how to refresh them. No slides file has been made; turn this into one when a date and audience are fixed.*

**The one sentence:** the hard part of this project was never the map. It was joining sources that disagree, saying how far to trust each fact, and keeping the data current with as little human review as is safe ([case study](case_study.md)).

## 90-second pitch (interview opener)

1. **What:** a free map of racket-sport venues in California and Nevada, for sports where a tennis court and a padel court are not the same pin. 10,288 venues; 41 of 82 sports have at least one ([scorecard](data_quality_trend.csv), 2026-10-29).
2. **How:** Python ingestion, dbt on DuckDB, one 2.45 MB JSON file on GitHub Pages. No server, no accounts, $0 hosting ([running costs](running_costs.md)).
3. **The interesting part:** I measure it. A labelled test set scores the place matcher (129 pairs, 0 wrong merges, 4 missed). A scorecard has stated service levels, and one is breached in public: 16.2% of venues have a real name against a 25% goal.
4. **The decision I am proudest of:** a model never merges anything. A deterministic script decides, and it has merged one routine PR so far (#410).
5. **Close:** "It is a one-person project at small scale. I can tell you exactly where that stops."

## 10-minute talk: eight slides

| # | Slide | Say | Proof on screen |
|---|---|---|---|
| 1 | The problem | Sources disagree: OSM has courts but few names, directories have names but not courts, clubs publish access rules only on their own pages. | [case study](case_study.md), "The problem" |
| 2 | The shape | Raw lands untouched, dbt cleans and tests, one export feeds a static page. | [architecture](architecture.md); live [dbt docs](../app/how-its-built.html) |
| 3 | You don't need a warehouse | Queried Overture's public Parquet in place: 743 MB fetched of 39.6 GB. A laptop file was enough; I never ran it on a warehouse, so no speed claim. | [article](articles/you-dont-need-a-warehouse.md), [benchmark](planet_scale_benchmark.md) |
| 4 | Trust is a data model | Confirmation scale (visited / operator / reported / inferred); every seed row carries `evidence` and `verified_on`; inferred data is labelled. | [data dictionary](../app/data-dictionary.md) |
| 5 | Measure the matcher | Gold set drove three rules, each judged by score not by eye. | [article](articles/entity-resolution-gold-set.md) |
| 6 | Models suggest, a script merges | Risk classes, path allowlist, diff caps, scorecard no-regression, kill switch. Hardened this month; a review found two gaps, now closed. | [article](articles/models-suggest-scripts-merge.md), [threat model](merge_gate_threat_model.md) |
| 7 | The pilot I killed | Aerial-imagery detection: 46% recall in Las Vegas, 0 new venues in two rescans, dropped on a stop rule. The review-queue ranker (86% leave-one-out accuracy, AUC 0.93, 90 labels) stayed, after I found it had learned "Tennis means reject" from skewed labels. | [article](articles/the-ml-pilot-i-killed.md) |
| 8 | What it costs, what is not proven | Recurring bill I can point to is $0; only the AI agents are capped ($20/month). Small scale, one writer, usage not measured yet. | [running costs](running_costs.md) |

Timing: slides 1–2 two minutes; 3–5 four; 6–7 three; 8 one.

## 5-minute screen-recording script

Open four tabs before recording. Press the load button on "Ask the data" first (35.7 MB) so the recording has no wait.

1. **Map (60 s).** Filter to padel. Open a pin and read aloud how its name is labelled (confirmed or inferred). Say: "this label is the product."
2. **How it's built (45 s).** Scroll the pipeline and the numbers. Say they come from `build_stats.json`, not typed in.
3. **Ask the data (90 s).** Run "How sure are the names?" (5,743 unnamed, 2,875 inferred, 922 confirmed or hand-curated, 748 business listings). Edit one query live, then run a deliberately wrong column to show the error. Say: "this runs in your browser on the same file the map reads; nothing is sent anywhere."
4. **Run history (45 s).** Show the scorecard trend and the agent-runs table, including its cost estimates and that the log can lag GitHub.
5. **Close (60 s).** Open the merge-gate threat model. Say what is still open (gaps 1 and 4–7) rather than ending on a win.

## Questions to expect, and honest answers

- **"Why DuckDB and not Snowflake?"** I first kept both runnable; when Snowflake access ended, nothing had run on it, so I retired it (ADR 0018). I have no head-to-head benchmark.
- **"Is 16.2% a real-name rate or a named rate?"** Real name = confirmed or hand-curated (922) plus business listing (748) = 1,670. The export's `named` count (4,545) also includes names inferred from a nearby park or school. Say which one you mean.
- **"Does it scale?"** Not shown. One reader, one writer, twice-monthly batches. For concurrent users or data past one machine I would add a warehouse.
- **"Has the auto-merge gate been tested in anger?"** It merged one routine PR (#410, 4 venues). Its classifier was tested on synthetic exports and six past commits. Gaps remain in the [threat model](merge_gate_threat_model.md).
- **"How many users?"** None measured yet. A beta round is planned for December; no usage numbers until then.
- **"Is the LLM page reader in use?"** Built with an exact-quote guard rail checked in code; not run at scale, waiting on a spend cap and precision bar.
- **"Could someone reuse it?"** There is a [fork guide](fork_guide.md) and an init script; a trial on a made-up region built 333 nodes with one data-dependent test failing, which the guide documents. No real extract for another area has been tried.

## Do not claim

- Terabyte-scale processing, streaming, or speed against a warehouse.
- Users, traffic or satisfaction.
- That the agents run unattended: refresh is run by hand until the owner schedules it.
- Anything about data from Google Places or other court apps; the project does not use it.

## Recheck on the day

- Venue and sport counts, service levels, tests: `python ingestion/build_stats.py` then read `app/data/build_stats.json`, or the last row of [`data_quality_trend.csv`](data_quality_trend.csv).
- Gold-set result: `python ingestion/eval_match_gold.py --check`.
- Ask-the-data question results: run the page, or `python ci/check_ask_the_data.py` for a pass/fail.
- Agent runs and cost: [`agent_log.csv`](agent_log.csv); open PRs and the gate's decisions on GitHub.
- Number of ADRs, models and seeds: [case study](case_study.md), "At a glance" (53 models, 34 seeds, 26 decisions as of 2026-10-29).
