# ML and AI: strategy, plan and discovery

Merged 2026-11-12 from `ml_strategy.md`, `ml_plan.md`, `ml_discovery_plan.md`; each is now a section below.

## ML and agents strategy: how AI takes over the project's work

Written 2026-10-21. A plan, not a decision: nothing here starts a scheduled task, spends money or changes a rule until the owner says so (CLAUDE.md, ADR 0019). It sits above three existing documents and does not replace them:
`docs/ml.md` (the ML phases and their results), `docs/self_service_plan.md` (which refresh steps a machine can own) and ADR 0017 / 0019 (the page reader, and when an agent may merge). Read those for detail; this page is the order, the architecture and the case for doing it.

### 1. The case for ML here (the short version)
RacketConnect is a data-quality problem on messy open data, run by one person. Three facts make ML a good fit, and each one is already measured in this repo:

1. **The bottleneck is reading and judging text, not computing.** The 116-row review queue, the facility scans, the `*-access` leads, the 482 pins that still lack a street, and every court count that is "on a page somewhere" all come down to "read a public page, find the sports, courts and address". That is what a language model does, and it is slow and context-hungry done by hand in a chat session.
2. **Every human decision is already a label.** About 170 rows in `place_sport_overrides.csv`, 129 hand-judged venue pairs in the match gold set, 34 hand-settled pages for the reader, and every closed GitHub issue are verdicts with evidence. Most projects have to pay for labels; this one produces them as a by-product of working. Each verdict makes the next model better, so review effort now buys automation later.
3. **The guard rails exist, so the risk is bounded.** The model proposes, deterministic code decides: the quote check drops any fact not verbatim on the page (`ci/check_page_reader.py`), the gold sets score every rule change (`make eval-match`), CI and the scorecard regression check block bad builds, and ADR 0019 says how a class earns auto-merge. ML here is never trusted on faith; it is trusted to the measured number.

**What the numbers say today** (all from this repo's own notes):

| Piece | Result | Reading |
|---|---|---|
| Review-queue ranker | 86% leave-one-out accuracy, AUC 0.93; "likely" calls right 93% | Good enough to order work, never to decide it |
| Reader, free rules engine | 96 facts on 34 pages, 0 failed the quote check, 0 conflicts with the seed; sport found on 31/34, court count 14/34 | High precision, low recall: the proof that the guard rail works, and the reason a model engine is the next step |
| Match rules vs gold set | 129 pairs, 0 wrong merges, 4 missed | Rules are already strong; a learned matcher is a challenger, not a rescue |
| Aerial detector | Hawthorne: ~2 new sites per city; Las Vegas: recall 0.46 | Works, low yield, parked |
| Scorecard | 7 of 8 SLAs met, 100% of venues seen in 35 days, 199 tests passing | The gates an agent must not break |

**What ML will not do** (so nobody oversells it): create data that exists on no page and in no dataset (a court count only the owner knows, a private club's rules), tell tennis from pickleball in aerial imagery, or make a fact "confirmed". Inferred stays inferred (ADR 0007); a model-found fact is a candidate until it passes the gates.

### 2. The honest answer to "should we build agents, or is there another way?"
Yes, build agents, but not one free-roaming agent. There are three ways to automate this project, and the right answer is the middle one, built on top of the first.

| Approach | What it is | Fits RacketConnect? |
|---|---|---|
| **A. Plain automation** | Scripts + `make` + CI + cron. No LLM. | Covers about two thirds of the runbook already (the "M" steps in `docs/self_service_plan.md`). Do this first and keep it as the spine. |
| **B. Narrow agents under deterministic gates** (recommended) | Several small workers, each with one job, a fixed output format, no tools beyond what it needs, and a merge gate it cannot change. The model reads and proposes; code verifies and decides. | Fits the "E" steps (evidence, quote) and issue handling. This is ADR 0019's design. |
| **C. One autonomous agent with open tools** | A general agent told "keep the project healthy". | No. It reads untrusted pages and issues, holds write access, and can't be audited or capped. Wrong for data the public reads. |

Why B and not "just more scripts": the hard 30% of the work (an issue written in free text, a club page phrased its own way, a closure the page only hints at) is exactly what rules can't read. The rules reader's recall (court count 14/34, access 0/17) shows the ceiling.

Why B and not C: the risk is a hostile page or issue steering the agent, a runaway bill or a bad bulk edit. B contains all three: the page-reading model has no tools, a gate script (no LLM) controls merging, spend and PR counts are capped, and a kill switch stops everything.

**The pattern every agent follows: observe -> propose -> verify -> decide -> learn.**

```
 inputs                    worker (LLM, no tools)        deterministic code            outcome
 issues / form reports --> triage agent  ----------+
 venue + lead pages -----> reader agent  ----------+--> quote check, schema check,
 link / closure checks --> watcher agent ----------+    second-model check, rebuild,   --> PR (class R0-R3)
 monthly extract --------> refresh script ---------+    diff cap, scorecard gate         --> merge gate --> auto-merge
                                                        ^                                   or owner (R3)
 labels: every accepted / edited / rejected PR ---------+---- docs/agent_log.csv ---> retrain, re-measure
```

### 3. Principles (carried over from the ADRs, plus three new ones)
- Model proposes, code decides. A model never merges (ADR 0019 section 1).
- Every fact carries an exact quote and a URL that code, not the model, found on the fetched page (ADR 0017).
- Honest labelling: where no person reviewed a fact the map says "checked automatically; a person audits a sample", never "reviewed" (ADR 0019 section 7).
- Public pages only, no owner logins, no Google Places data, project User-Agent only, no personal data, links out only.
- Cheapest engine that clears the bar: free rules, then a small Claude model, then bigger only if a measured gap needs it (bare-minimum budget; $20 a month cap).
- **New: a model ships only if it beats a stated baseline on a held-out set**, with the interval reported (see section 6). No "it looked right on the pages I tuned it on" (the rules engine's current numbers are tuned on the pages they are measured on, and the notes already say so).
- **New: start the track-record clock early.** ADR 0019 makes auto-merge depend on N clean PRs (R0: 6, about 3 months; R1: 15; R2: 30 per field type). Engineering is not the slow part; the clock is. Every week stage 0 does not run delays autonomy by a week.
- **New: one place to measure.** A monthly `docs/ml_scoreboard.csv` line (section 6) so progress and regressions are numbers, not impressions.

### 4. ML tracks: what, why, priority
Ranked by value to the self-service goal against effort and risk. "Gold" = the labelled set that measures it.

| # | Track | What it does | Gold / baseline | Value | Effort | Verdict |
|---|---|---|---|---|---|---|
| 1 | **Reader** (LLM page reading, ADR 0017) | Turns a venue or facility page into fixed fields with quotes: sports, courts per sport, indoor/outdoor, access, street address, booking link | 34 hand-settled pages; rules engine as the baseline | Very high: unlocks R2, the review queue, scans, leads, non-home addresses | Medium (script exists, needs the model engine + cap) | **Do first** |
| 2 | **Feedback triage** | Classifies and dedupes issues, form reports and beta feedback; extracts the proposed row; screens for spam and injection; drafts the reply or the seed edit | Past issues + form rows, hand-labelled once | Very high: replaces the `approved` label, the main human gate | Medium | **Do second** |
| 3 | **Priority ranker, widened** | Today ranks the review queue. Extend to "what should the agents read or recheck next": stale venues, leads, unverified fields; calibrate its probabilities | 173 override rows; leave-one-out | High, cheap: makes every agent spend its budget well | Low | **Do alongside 1** |
| 4 | **Extract drift / anomaly guard** | Flags an extract or build that looks wrong before it ships: per-sport and per-area count shifts, a new Overture release, sudden address-fill changes, test-set drift | Backtest on past extracts (trend CSV, snapshots) | High: this is what lets R0 refreshes auto-merge safely | Low | **Do before R0 goes live** |
| 5 | **Watcher** (page-change and closure signals) | Detects a venue page that changed, went dead, or says "permanently closed" / "coming soon" / "now open"; rechecks leads and events | `closed_places.csv`, lead outcomes, padel rechecks | Medium-high: covers rechecks (item 4, 8 on the roadmap) | Medium | After 1 |
| 6 | **Learned matcher** (Overture/OSM entity resolution) | A gradient-boosted pair classifier as a challenger to the hand rules | Match gold set (129 pairs, 0 wrong, 4 missed) | Low now: rules leave little room; the gold set is also small | Medium | **Shadow only.** Adopt only if it beats the rules on a fresh sample without a wrong merge |
| 7 | **Supply-gap and demand view** (`mart_supply_gap`) | Courts per 10,000 residents by sport and area (Census, no key) plus anonymous click signals | Needs beta traffic (GoatCounter) | Medium, product-facing: a story for the beta and for "discover new sports" | Medium | After beta data exists; ADR first (privacy line in `ml.md`) |
| 8 | **"Try something new" recommender** (DROPPED 2026-10-21, ADR 0015 amendment) | Suggests sports like the ones you play, using `ref_sport_fit` and `sport_also_played`; no accounts, no tracking | Hand check on 10 sport pairs; click-through in beta | Medium, directly serves the mission (ADR 0015) | Low | After beta; a similarity table, not a deep model |
| 9 | **Aerial court detector** (phase 3) | Finds courts in no dataset | OSM pitches | Low: single-digit new sites per city, mostly private, needs a person per site | High | **Parked.** Revisit only after 1-5, with fine-tuning and recall by sport |

Notes on the table:
- **Tracks 1 and 3 reinforce each other.** The ranker picks which pages the reader reads first; the reader's accepted facts become new ranker labels. That is the flywheel in one loop.
- **Track 4 is the quiet enabler.** ADR 0019 gates cover a build that fails; they do not cover a build that passes and is wrong (for example an Overture release that silently drops a category). A drift check closes that hole and is cheap statistics, not deep learning.
- **Track 6 is deliberately low.** It is the most "ML-looking" idea and the least useful today. Say so out loud so effort goes where the measured gap is.
- **Local open model** (free middle path in `docs/archive/session_digest.md`): try it for track 1 only if the paid engine's cost or the cap becomes the limit. Same `verify()`, same quote check.

#### Track 1 in detail: the reader roadmap
1. **Freeze the reader gold set.** The 34 hand-settled pages, plus 30 fresh ones nobody tuned on (held out for good). Record per field: expected value or "not on page".
2. **Add the model engine** (`--engine claude`), same fixed fields, same quote check. Dry run prints pages and tokens first; abort if the estimate exceeds the remaining weekly cap (ADR 0019 numbers). Cache by URL + date.
3. **Compare three engines on the held-out pages:** rules, small Claude model, (optional) local model. Report field precision, recall, and no-quote share, per field type (sport, courts, setting, access, address, booking link).
4. **Decide per field, not per engine.** Sport and setting may clear the bar with rules alone; access and address may need the model. Each field type earns its own class (ADR 0019 R2, per field type).
5. **Wire it to targets:** the review queue first (116 rows), then `*-access` leads, club-named venues, the 482 non-home pins without a street (ADR 0016 and the home-privacy rule still apply: home-like pins never get an inferred street), then city rec directories.
6. **Pages the reader can't reach** (3 of 20 block bots; robots.txt is respected) stay hand review. Don't engineer around them.

#### Track 2 in detail: the triage agent
- Inputs: `venue-change` issues, the community form sheet (`make sync-reports`), and later beta feedback.
- Steps: classify (change request / bug / feature idea / duplicate / spam / looks like prompt injection) -> if a change request, fetch the cited public page with the reader and quote-check the claim -> propose the seed row or ask the reporter exactly what is missing -> post the draft; stage 0 means a person still adds `approved`.
- Untrusted input: issue text is data. The classifier has no tools, returns a fixed label and fields, and can't act on instructions inside the issue (ADR 0019 section 6).
- Gold: label every past issue and form row once (a short session), hold some out, measure class accuracy and the share of drafted rows the owner edits.
- Beta use: the same agent groups beta feedback into themes and drafts the RICE table (`docs/feedback.md`), so the owner reads a summary, not 40 messages.

### 5. Agent roster
Each agent has one job, a fixed output and a class from ADR 0019. "Runner" is where it lives (section 7).

| Agent | Job | Engine | Output | Class | Runner | Starts |
|---|---|---|---|---|---|---|
| **refresh** | Runbook steps 1, 2, 4-9: sync sheet, load, build, quality, export, PR | Script + `make` (no LLM); a model only to explain a failed gate in the PR body | One PR per refresh, scorecard line | R0, R1 | Local (needs `data/raw`) | Draft mode as soon as the owner OKs a schedule |
| **triage** | Issues + form reports (+ beta feedback) | Small Claude model + reader | Draft seed edit with quote, or a question to the reporter | R2 (from issues) | Actions or local | Draft mode first |
| **reader** | Venue and facility pages -> candidates | Rules, then Claude | `docs/reader_candidates.csv`, then seed PRs | R2 per field type | Local or Actions | After the pilot clears the bar |
| **watcher** | Link health, closures, padel and event rechecks, social series | Script + reader | Re-date PRs (R1), status change proposals (R3 if closing) | R1, R3 | Actions | After reader |
| **auditor** | Weekly digest: sample 10% of auto-merged PRs, re-check against the page with a second model | Claude, independent of the proposer | Digest to the owner; demotes a class on a wrong fact | n/a | Actions | At stage 1 |
| **merge gate** | Decides auto-merge | **No LLM.** A script on required checks | Merge or "escalate to owner" | n/a | Actions | Shadow mode first |

The merge gate and the kill switch are not agents on purpose: the thing that decides must not be the thing that can be talked into it.

### 6. Evaluation and the ML scoreboard
This is the part that makes ML honest on a small dataset, and the part to show anyone being sold on it.

- **Held-out sets stay held out.** Reader pages and triage issues that were used to tune a rule never count toward the number reported.
- **Report intervals, not just percentages.** 98 correct of 100 sounds like 98%; the 95% interval is roughly 93% to 99%. ADR 0019's R2 bar ("95% on at least 100 fields") should be read as the point estimate, and the plan should also require the **lower bound** to stay above 90% before auto-merge. Owner decision (suggested, not yet in the ADR).
- **Skew checks.** The ranker's first run learned "Tennis counts against" because every Tennis label was a reject. Every model gets a per-sport / per-source breakdown, not just a headline.
- **Compare to a baseline** (rules for the reader and matcher; "do nothing" for the ranker; last month's counts for the drift check).
- **Model card per model** in `docs/models/<name>.md`: what it is for, data and labels, metrics with date, known failure modes, who may use its output. One short file each.
- **`docs/ml_scoreboard.csv`**, one line per monthly refresh, appended by the refresh agent (a new file, so no merge collisions, same idea as `docs/data_quality_trend.csv`):

| Column | Meaning |
|---|---|
| `date` | Run date |
| `reader_precision`, `reader_recall`, `reader_no_quote_pct` | On the held-out reader set |
| `ranker_loo_acc`, `ranker_auc`, `queue_size` | Review queue ranker |
| `match_wrong`, `match_missed` | `make eval-match` |
| `agent_prs`, `agent_accepted_unchanged_pct`, `agent_reverts` | From `docs/agent_log.csv` |
| `auto_merge_classes` | Which classes are at stage 2 |
| `spend_month_usd` | Against the $20 cap |
| `owner_review_min` | Minutes the owner spent reviewing this period (self-reported, one number) |

`owner_review_min` is the goal metric. Today it is unmeasured; measuring it for two months is itself an early deliverable.

### 7. Where agents run (the open question in ADR 0019)
Raw CSVs live in the main checkout's `data/raw` and an extract takes about 15 minutes and reads S3, so a runner that can't see that folder can't refresh. That is the one real engineering constraint.

| Option | Pro | Con |
|---|---|---|
| **Local scheduled task** (the Claude app's scheduled tasks or Windows Task Scheduler running `claude -p` / a script) | Works today; sees `data/raw` and `courtconnect.duckdb`; no secrets in the cloud | Needs the machine on; one bad night means a missed run (hence the "no refresh PR in 20 days" alert) |
| **GitHub Actions** (cron + Anthropic API) | Always on; the PR, CI and merge gate live there already; secrets in repo settings | No `data/raw` or built DuckDB; seed PRs also need `venues.json` regenerated |
| **Claude cloud routines** | No infrastructure to run | Same data problem as Actions; another system to trust |

**Recommendation (a refinement of the ADR's hybrid):**
1. **Heavy refresh stays local**, monthly, scheduled once the owner agrees. It owns extract, load, export.
2. **Seed-only agents (triage, reader, watcher) can move to Actions** because they read the web and edit seeds, and CI already validates seeds against fixtures. The blocker is `app/data/venues.json`: it has to be regenerated after a seed change. Cleanest fix: a **post-merge job** that rebuilds and commits the export (needs the raw tables in object storage or as a release asset; check size first). This removes the venues.json collision between PRs, which the notes call out as the main source of merge trouble. It also needs its own small ADR.
3. **Until then** run triage and reader locally in draft mode. It costs nothing extra and starts the clock.

### 8. Roadmap
Phases use order and exit tests, not dates: the beta dates are still TBD (December in `CLAUDE.md`, 2026-11-02 in `ml.md`). One task per session, as the project rules say.

#### Phase 0: groundwork, no spend, nothing scheduled (now)
Each item is a small PR or a single session.
1. `docs/agent_log.csv` (columns: date, agent, class, pr, outcome = unchanged / edited / rejected / reverted) and a README paragraph on how to fill it.
2. Merge gate script in **shadow mode** (computes "would auto-merge" for a PR, posts nothing). Includes the path allowlist per class and the diff caps from ADR 0019.
3. **Drift check** (track 4): a script that compares a new extract and build against the last N, fails loudly on a shift beyond a stated threshold, added to the refresh runbook before step 8.
4. **Reader gold set** frozen (track 1 step 1) and **triage gold set**: label past issues and form rows.
5. Start measuring `owner_review_min` and `docs/ml_scoreboard.csv` with what exists (ranker, match, scorecard).
6. Move the CLAUDE.md "Current status" lines into the scoreboard / trend CSV, as `self_service_plan.md` already suggests, so agents don't edit a shared file.

**Exit:** a shadow gate verdict can be produced for any PR; the scoreboard has its first line; both gold sets exist.

#### Phase 1: reader and triage pilots (needs the owner's key and cap)
1. Owner sets the API key in `.env` and confirms the cap ($20 a month, $5 a week per ADR 0019) and the precision bar.
2. Reader Claude engine pilot on the held-out pages (track 1 steps 2-4). Write the result into `docs/models/reader.md`.
3. Triage agent in draft mode on live issues: it comments or drafts; a person still labels `approved`. Log every outcome.
4. Widen the ranker (track 3) to rank reader targets; retrain after each accepted batch.

**Exit:** field precision (with interval) per field type; triage draft accepted unchanged on at least 70% of change-request issues (suggested); cost per accepted fact known.

#### Phase 2: draft-mode agents on a schedule, shadow gate on (beta window)
1. Owner approves a schedule (nothing starts without it). `refresh` agent runs the runbook and opens the PR; a person merges (stage 0).
2. Reader works the review queue, `*-access` leads and club-named venues; every fact is a PR or a candidate row with a quote.
3. Triage handles beta feedback and issues; the synthesizer produces the RICE draft.
4. Shadow merge gate runs on every agent PR; compare its verdicts with the owner's merges.
5. Weekly auditor digest begins, sampling the PRs.

**Exit:** at least 6 refresh PRs in the log; zero gate false negatives in shadow; the owner's review time is down against Phase 0's baseline.

#### Phase 3: promote what has earned it (earliest around Q1 2027)
1. R0 and R1 switch to auto-merge only when their ADR 0019 numbers are met and the owner switches them on. R0 needs 6 clean PRs plus 3 shadow runs, so about three months of stage 0 first.
2. R2 per field type: only fields whose precision and interval clear the bar.
3. Watcher agent live (closures stay R3; the page must state the closure).
4. Product: supply-gap view, using beta data (each behind an ADR where it touches privacy).
5. Learned matcher as a shadow challenger on the next gold sample; adopt only on a clear win.

#### Later (each needs its own ADR first)
Link discovery beyond held URLs; PDFs and images (directory sites that forbid reuse stay off limits regardless); a local open model for the reader; a read-only MCP server over `venues.json`; aerial v2 with fine-tuning; moving to the `courtconnect` repo name; moving `data/raw` to object storage.

### 9. Budget
- **Cap:** $20 a month, $5 a week (ADR 0019). A dry run aborts if its estimate exceeds the week's remainder.
- **Scale:** the 16-page rules pilot was about 28,500 input tokens, so a pilot of that size is cents. A 1,000-page sweep is on the order of 1.8 million input tokens; price it against the current rates for the chosen model before running (rates change, so this page does not quote them).
- **Spend order, cheapest first:** rules (free) -> cached model reads of pages that rules couldn't settle -> second-model check only on facts that would otherwise be applied -> the weekly audit sample. Pages are cached by URL + date, so a page is read once.
- **Free first:** scikit-learn, DuckDB, Census boundaries, Planetary Computer and OSM stay the default. Paid APIs are optional and capped (project budget rule).

### 10. Risks and how the plan answers them
| Risk | Answer |
|---|---|
| A hostile page or issue steers an agent | Reader/triage have no tools; fixed output; gate script decides; issue text is data (ADR 0019 section 6) |
| A confident wrong fact reaches the map | Quote check, second-model check for R2, weekly audit sample, one wrong fact demotes the class |
| A build that passes tests but is wrong | Drift check (track 4) and the scorecard no-regression gate |
| Small labelled sets give misleading accuracy | Held-out sets, intervals, skew breakdowns; tuned-on numbers are labelled as such |
| Runaway cost | Weekly cap, dry-run estimate, cache, kill switch `AGENTS_ENABLED` |
| Privacy: home-like pins, personal data in issues | Unchanged rules (address privacy, ADR 0016); reader never proposes a street for a home-like pin; agents never copy contact details into seeds |
| Terms of service of pages and directories | Public pages only, robots.txt respected, project User-Agent, reuse-forbidden directories stay off limits |
| Over-trusting the "AI" label with users | About text says "checked automatically; a person audits a sample", never "reviewed" |
| Single owner is also the single point of failure | Alert if no refresh PR in 20 days; every change is a PR with a revert drill |
| ML time displaces mission work (more sports, more venues, social) | Phase 0 is small; agents exist to free the owner for mission work, and each phase has a stop test |

### 11. Decisions needed from the owner
1. **Approve Phase 0** (no spend, nothing scheduled). This is the only decision needed to start.
2. API key and cap for Phase 1; the reader precision bar, and whether to add the "lower bound above 90%" rule.
3. When agents may be scheduled (Phase 2), and whether the first runner is local.
4. Whether to write the two ADRs this plan implies: **ADR 0022 ML evaluation standard** (held-out sets, intervals, model cards, scoreboard) and **ADR 0023 agent runtime** (where agents run, post-merge export job, raw data in object storage). Both are drafts for the owner to accept, like ADR 0019.
5. Which review-time goal to aim for. Suggested: measure two months first, then set a target (for example under an hour a month of routine review by the end of Phase 3, escalations excluded).

### 12. What to do first
Start Phase 0 item 1, 2 and 4 (the log, the shadow gate, the two gold sets). They cost no money, need no schedule, and are the prerequisites for every later step: without the gold sets there's nothing to measure a model against, and without the log the track-record clock never starts.

## ML plan (after the beta)

The umbrella strategy (tracks ranked by value, agent roster, evaluation scoreboard, phased roadmap) is `docs/ml.md`; this page keeps the phase detail and results.

Three steps, cheapest first. Each one only **suggests**; a person confirms before anything reaches the map (honesty rule). Start after beta findings (from 2026-11-02).

### Phase 1: review-queue ranker (quick win, ~1 session)
- Labels: confirm/reject rows in `transform/seeds/place_sport_overrides.csv`.
- Clues: words in the name, Overture category, nearby OSM tags, distance to the nearest OSM court, website domain, rules_v2 confidence.
- Small scikit-learn model -> `review_priority` for `mart_sport_evidence.needs_review`. Clear-cut cases first; never auto-confirms.
- **Built 2026-10-14** (started before the beta): `ingestion/rank_review_queue.py`, `make rank-review`, needs `pip install -r requirements-ml.txt`. Writes `docs/review_priority.csv` with `review_priority`, `model_guess` (likely_confirm / likely_reject / unclear), `p_confirm`, and the top three `reasons`. It prints a leave-one-out check, where each label is guessed by a model that never saw it.
- 2026-10-17: rows whose domain is flagged dead (`website_overrides` or the DNS check) get `website_status` = dead and sort last, since a dead site cannot settle the sport.
- Use: in a review session, start at `review_priority` 1. Check the venue's own page as usual and write the verdict in `place_sport_overrides.csv` (with `evidence`, `verified_on`). Re-run after each batch: new labels retrain it.
- First run (61 labels: 37 confirm, 24 reject; queue 233): leave-one-out accuracy 82%, AUC 0.88; when it says "likely" it was right 85% (47 of 61). Queue split: likely_confirm 104, unclear 116, likely_reject 13. The top ~40 rows (club or association names whose website contains the sport, e.g. table tennis and pickleball clubs) are good first picks. The reject side is weak: most rejects so far are "X Beach Tennis" place names, so it has also learned odd rules ("OSM court within 100 m" counts against). Shop and apparel names are its reliable reject clue. More rejects from other sports will fix this; treat `likely_reject` as "check first", not "probably wrong".
- Batch 3 (2026-10-15, top 25 + 10 weak-side rows): 18 confirms + 4 rejects from public pages, 13 unclear (dead, blank or hijacked sites, or pages that don't settle it). Now 83 labels (55/28), queue 212: leave-one-out accuracy 86%, AUC 0.93, 'likely' calls right 93%. The top 25 were 17 of 17 right where a page settled it, and 4 of the 5 settled weak-side rows were rejects. New skew: every Tennis label so far is a reject, so 'sport=Tennis' now counts against (Tennis is 25 of the 41 likely_reject rows, e.g. Rancho Bernardo Swim & Tennis Club). Next batch: confirm some real tennis venues first.
- Batch 4 (2026-10-15, tennis skew fix): 7 Tennis confirms from clubs' own pages (Nellie Gail Ranch, Deep Canyon, Peninsula TC, Cambria TC, South Bay TC, Darling TC, Toluca Lake), 5 unclear. Now 90 labels (62/28), queue 205: Tennis likely_reject 25 -> 4 (likely_reject overall 41 -> 21, now mostly Basque Pelota 9 and Pop Tennis 7). Leave-one-out unchanged at 86% / AUC 0.93.
- Batch 5 (2026-10-15, Basque Pelota / Pop Tennis likely_reject, 16 rows): all but one are OSM-only (no place_id), so verdicts went to `osm_court_sport_overrides.csv` (rejects: Nunez Park pelota = outdoor racquetball per the city; Lair of the Golden Bear paddle_tennis = pickleball per the camp page) and `manual_venues.csv` (confirms: Kern County Basque Club fronton, Laguna Woods Village Paddle Tennis Club, 7 courts). Queue 205 -> 201. Labels stay 90: the ranker learns only from `place_sport_overrides`, so OSM-only verdicts don't train it. 12 rows left for the owner (schools' pelota tags, separate paddle_tennis polygons at parks/schools, Chino and South SF Basque courts).
- Rules: the guess never goes into dbt, the export or the map. The rules_v2 confidence score is left out on purpose, because human overrides already feed it (that would leak the answer).

### Addresses for pins without one (not ML; do before phase 2)
On 2026-10-15 about 90% of venues had no street address (CA 9,010 of 9,991; NV 471 of 533), mostly OSM park and school courts. The owner asked for an address on every court.
- This is a lookup, not a model: take the nearest **Overture addresses** point (open data, same release we already load; no API calls) or reverse-geocode with Nominatim (OSM; 1 request a second, so ~3 hours for both states, cache the results). Never Google (ADR 0005).
- Show it as "Nearest address (inferred)", with the distance; skip it when the nearest address is more than ~150 m away, since park courts can sit far from the park's street address.
- Directions don't need it: the popup's Google Maps / Apple Maps links already go to the pin's coordinates.
- Where ML helps: phase 2 can read a park's own page for its street address (with a quote), which beats the nearest-point guess.

**Planned build (decided 2026-10-16). Step 1 (tiers 1-2 + home check) BUILT 2026-10-16, results below.** Fill only venues with no street address, first hit wins, never overwrite a real address:
1. Address tags already in OSM (`addr:housenumber` + `addr:street` on the court, or its parent park/school). Free and exact.
2. Nearest Overture address point within ~150 m (spatial join in DuckDB, no API calls). Farther = leave blank.
3. Nominatim reverse geocode for the leftovers only, cached in a seed/CSV (1 request a second, proper User-Agent, never re-query).
4. Official page with a quote, by hand in `manual_venues.csv` for high-value venues (parks, public facilities).
- Store `address_source` (`osm`, `overture_nearest`, `nominatim`, `official_page`) and `address_distance_m`. The popup labels anything other than `osm` or `official_page` as "Nearest address (inferred)". Likely a new `int_venue_address` model plus an export field.
- **Privacy rule (owner, 2026-10-16): residential homes show the city only, never the street address.** Check this before filling, so the street is never stored for those pins. Apartment complexes are fine (full address).
  - Home signals (any one): OSM `building=house|detached|residential` on or around the court; `landuse=residential` with no name, operator or website; `access=private` on an unnamed court; the Pop Tennis import's private-home type; an Overture "residential" / "private residence" category.
  - Apartment exceptions (full address): `building=apartments|dormitory`, `residential=apartments`, names containing Apartments / Villas / Condos / Townhomes / Residences / HOA / Community, clubhouse or amenity courts inside a complex.
  - Unclear cases (e.g. unnamed private court in a residential area): fail safe, city only. City comes from OSM `addr:city`, the Overture locality, or the venue's existing city.
  - Gap to check: city-only text does not hide the pin, and the Directions links still use exact coordinates. The Pop Tennis importer already never imports private homes, so first count how many home-like pins are on the map today; if any, offset/round their coordinates or remove them.
- First step when picked up: build tiers 1-2 + the home check, then report the count of flagged pins and how many pins are still blank before deciding whether tier 3 is worth running.

**Step 1 results (2026-10-16; `int_venue_address`, `ingestion/extract_overture_addresses.py`, `make extract-addresses`).** Of 10,236 venues, 9,227 had no address.
- Tier 2 (nearest Overture address within 150 m; the extract keeps address points within ~440 m of any pin, 5.4 M rows, ~35 s): 2,939 pins filled (median 55 m, 90th percentile 106 m), shown as "Nearest address (inferred)". Tier 1 for the court's own tags was already in `dim_venue` (102 pins, `address_source` osm); the Overture place address is `overture_place` (907). Tier 1 for the *parent* park/school is not possible yet: `osm_parents` has no `addr:*` columns (needs an Overpass re-extract).
- Home check: 5,755 pins are home-like (1,224 with an access=private court, 20 customers/members, 4,511 unnamed with no access tag), because OSM `landuse`, building around the court and Overture residential categories are not in the data (only `building` on the court itself, none are houses). The rule is therefore the fail-safe one: an unnamed venue with no court tagged public = city only. 5,349 of them had a nearby address that was withheld; 548 other pins are blank (no address point within 150 m). 16 home-like pins already show a street today (tagged on the OSM court): kept (owner, 2026-10-16: OSM publishes it), proposal closed.
- Still blank after step 1: 6,287 pins (5,739 home-like by design, 548 not). City filled for 8,010 pins that had none.
- Directions links use the exact pin coordinates, so the home-like pins (unnamed courts, 1,224 of them tagged private) are still exactly locatable. Decided (owner, 2026-10-16): no rounding or hiding. The coordinates come from OSM, which publishes them, same rule as OSM-tagged streets; RacketConnect only never infers a street for these pins. Proposal closed.
- Tier 3 (Nominatim) mostly adds nothing for the home-like pins (they must stay city only), and for the 548 others it covers the gap in rural spots; worth running only for those 548.
- **Tier 3 sample (2026-10-16; `ingestion/reverse_geocode_blanks.py`, cache `transform/seeds/nominatim_addresses.csv`, `make reverse-geocode`).** Recount after step 1: 559 non-home pins have no address (CA 283, NV 276; 449 named by an enclosing park or school, 79 manual, 20 court-named); 5,739 home-like pins stay city only; 16 home-like pins with a street are OSM-tagged (6) or the Overture place's own address (10): kept, per the owner rule above (OSM publishes it). A random 25-pin Nominatim sample (1 request a second, project User-Agent, pin coordinates only) gave 2 house-number addresses (8%; Sunset Park 7 m, Lt. Erik Lloyd Memorial Park 0 m), 22 street-only hits (nearest road or trail, not an address: not used), 1 over 150 m. Only `status = address` feeds `int_venue_address` (`address_source = nominatim`, labelled "Nearest address (inferred)"). The owner approved the full run the same day: all 559 pins queried (single thread, ~1.1 s apart), **83 addresses (15%)** filled as `nominatim`, 433 street-only (not used), 43 over 150 m; 6,228 pins stay blank (5,739 by design). Rerun `make reverse-geocode` only for new blanks (cached rows are never re-queried unless the pin moved). Policy note: this was a one-time, single-thread job on specific pins, not a grid sweep; do not repeat it in bulk. Cheaper alternative with no API: a street-level 'near <road>' line from OSM roads, or phase 2 (read the park's own page).

### Business use case: venue demand and capacity (idea 2026-10-16, not started)
Question: could the map help show where players and spectators are underserved, and predict whether a new venue nearby would ease the flow? That needs demand data (people counts, views, referrals, plays, ticket sales), and the constraint is that everything must be free.
- Free signals we can already get or add without paying: GoatCounter page counts (ADR 0013; per-venue popup opens and Directions / link-out clicks as events, no personal data), the suggest-a-change and issue counts per venue, and the public court counts we hold.
- Free public data that proxies demand: Census / ACS population by tract (age, density), OpenStreetMap park and school density, Strava Global Heatmap is not usable (terms), but city open-data portals sometimes publish court reservation counts, and national bodies publish club membership (USTA, USA Pickleball place-to-play counts).
- Method (cheap first): courts per 10,000 residents within 2 km / 10 min drive by sport (supply ratio), then add observed interest (opens/clicks per venue) as a second signal; flag tracts with high population, no courts, and clicks from the area. A map-view count of searches in an area with no venue is a free "unmet demand" signal.
- Not possible for free: ticket sales, foot traffic inside venues, individual player tracking (also a privacy line we should not cross: aggregate, anonymous counts only, ADR first).
- Next step if wanted: ADR + a `mart_supply_gap` model (tract population from Census, no API key) and a GoatCounter events plan; plan only, no code.

### Missing courts at known parks (owner report, 2026-10-15)
Manhattan Heights Park (Manhattan Beach) has at least 2 pickleball and 2 tennis courts; OSM tags only the 2 tennis courts, so pickleball was missing until the owner reported it (`manual_venues.csv`). A fresh `make extract` would not fix this: the data is not in OSM or Overture. Likely many parks look like this (pickleball lines painted on tennis courts, never tagged).
- Phase 2 (city park pages, `docs/public_facility_scan.md`) and phase 3 (aerial photos) are the routes to these. Pickleball lines on a tennis court are hard to see at NAIP resolution, so pages come first.
- Cheap check meanwhile: a city-by-city list of parks with OSM tennis courts but no pickleball tag, checked against each city's own park page (start with the South Bay cities).

### Phase 2: LLM reads public pages (ADR first)
- Pages: Overture places with a website and no sport yet, `*-access` / club-named leads, city rec directories (`docs/public_facility_scan.md`), chain pages (`docs/gym_chain_scan.md`).
- Public pages only, respect robots.txt, no logins (ADR 0007), no Google Places (ADR 0005).
- The LLM returns fixed fields (sports, court count, indoor/outdoor, access, booking link), each with an exact quote; code drops any field whose quote isn't on the page.
- Output: a staged candidate CSV marked inferred, approved in bulk into seeds. Measure precision against the hand-checked overrides.

### Phase 3: courts in aerial photos (pilot)
Finds courts that are in no dataset and on no web page (unmapped park, school, apartment and HOA courts).
- Imagery: NAIP (USDA, public domain, about 0.6 m per pixel), read through Microsoft Planetary Computer's public STAC (no account needed). A tennis court is about 40x18 pixels; a pickleball court is about 22x10, so it is harder to spot.
- Labels at no cost: existing OSM `leisure=pitch` court shapes (tennis, pickleball, basketball as hard negatives).
- Model: small object detector trained on image tiles; prefer permissively licensed ones (torchvision), since Ultralytics YOLO is AGPL.
- Pilot area: one city (Hawthorne, which matches the public facility pilot) and then one Las Vegas zip code. Report precision and recall against OSM before scaling up.
- New detections (not in OSM) -> candidate list -> owner checks on imagery -> **add to OSM** (ADR 0011 edit link) -> they arrive with the normal extract. RacketConnect stores no new data model, and OSM gets better too.
- Imagery shows a court shape, not sport or access: a candidate is "court here, sport and access unknown" until a page or a person says more. Lines alone can't tell tennis from pickleball, and private yards/homes are never added (same rule as the Pop Tennis importer).

#### Hawthorne pilot result (2026-10-16)
`ingestion/oneoff/aerial_pilot.py` (stages `osm`, `chips`, `train`, `detect`; own venv, see `requirements-ml.txt`). NAIP 2022 at 0.6 m via the public Planetary Computer STAC; torchvision Faster R-CNN with a MobileNetV3 backbone (BSD), CPU only, 8 epochs (~80 min).
- **Training data came from outside Hawthorne.** OSM maps only 9 tennis courts there, too few to train on, so the model learned from 731 chips (256 px) in the surrounding LA basin (2,466 racket-court boxes; basketball and other pitches as hard negatives) and Hawthorne is the untouched test area. OSM pitch polygons are the labels, so OSM drawing errors (one polygon around several courts) are learned too.
- **Results on Hawthorne vs OSM** (9 OSM tennis courts, IoU >= 0.3): score >= 0.5 gave 14 detections, 8 matched OSM (recall 8/9 = 0.89, precision against OSM 0.57); >= 0.3: 17 detections, recall 0.89; >= 0.7: recall 0.44; >= 0.9: nothing matched (the model is under-confident). Chip-level check on 81 held-out training-area chips: 195 hits, 101 false, 81 missed.
- **"Precision against OSM" understates it.** The 6 unmatched detections: 5 are racket-court candidates in no OSM pitch (`docs/aerial_candidates_hawthorne.csv`), 1 overlaps a basketball pitch. I looked at the 5 on the imagery: all are real tennis courts. Four are a multi-court school tennis complex next to a school (probably several courts, one box each, overlapping) and one is a single court inside an apartment/townhouse complex (private-looking; the CSV says do not add it to OSM without a public source). So 2 new sites, not 5.
- **Dimensions are rough.** Boxes are 12-27 m on a side, because the model copies OSM's habit of drawing one box around two or more courts. A single tennis court is 23.8 x 11 m (36 x 18 m with run-off), so treat `long_side_m` / `short_side_m` as the size of the detected box, not of one court.
- **Cannot do:** sport (tennis vs pickleball vs padel looks the same at this resolution), access, or indoor courts. Candidates are "court here, sport and access unknown", `status` inferred, and never go into seeds or `venues.json`.
- **Verdict:** the approach works for tennis-sized outdoor courts, but a pilot of this size (one city, 8 epochs, no tuning) finds about 2 new sites in a city of 9 mapped courts. Cost: ~2 sessions of build time, ~80 min CPU training, ~25 MB imagery. A metro-wide run would need merging of neighbouring boxes into one site per complex, a public/private filter from OSM landuse, and a person checking each site on the imagery before anything goes to OSM. Worth continuing with one Las Vegas zip as planned, but expect single-digit new sites per city, not hundreds.
- Reproduce: `python ingestion/oneoff/aerial_pilot.py osm && ... chips && ... train && ... detect` (imagery and model cache under `data/aerial/`, git-ignored).

#### Las Vegas pilot result (2026-10-16)
Same script, now with `--area NAME --bbox S,W,N,E`, run on a 5.4 x 6.7 km area in the middle of zip 89123 (south Las Vegas; bbox 36.01,-115.17,36.07,-115.11; hand-drawn, not the zip boundary). NAIP 2022 on the same STAC, EPSG:26911. The Hawthorne model was used **unchanged, no retraining or fine-tuning**. Added: detection boxes within 40 m merge into one site; OSM context (park/school/sports vs residential/none) sets the public/private note; one crop PNG per candidate.
- **Test set:** 57 OSM racket pitches (33 tennis, 24 pickleball) in 17 sites. 2,322 tiles, 167 raw detections.
- **Recall vs OSM is much lower than Hawthorne:** score >= 0.3: 42 boxes, 26 matched OSM (precision 0.62, recall 0.46; 13 of 17 OSM sites found); >= 0.5: 29 boxes, 24 matched (precision 0.83, recall 0.42; 12/17 sites); >= 0.7: recall 0.28. Nothing reaches 0.9. I did not break recall down by sport, so I cannot say whether the misses are the 24 pickleball pitches (smaller, often painted on tennis courts), or desert surface and lighting that differ from the LA training area; both are hypotheses.
- **Candidates (score >= 0.5, on no OSM pitch):** 4 sites, 1 box each. Spot check on the crops (small, 0.6 m): 001 a real blue tennis court in a condo complex with pool; 003 a court-like rectangle between apartment buildings (plausible); 002 a grey rectangle on a lot beside a house (unsure); 004 a parking lot (false positive). So about 2 likely real courts, both private-looking (residential context); none is in a mapped park or school. Nothing here is a lead for the public map without a public source.
- **Verdict:** at this setting the Hawthorne model is not good enough for Las Vegas as is: it finds under half of mapped courts and about 2 residential candidates per 36 km2. If continued, fine-tune on Las Vegas chips outside the test area first (not done), and check recall by sport. Everything stays `inferred`; nothing is in seeds, `venues.json` or the map.
- Output: `docs/aerial_candidates_lv89123.csv`. Reproduce: `ingestion/oneoff/aerial_pilot.py osm|mosaic|detect --area lv89123 --bbox 36.01,-115.17,36.07,-115.11`.

#### Downey/Norwalk and Elk Grove rescans (2026-10-27)
The script now picks the UTM zone from the bbox (10N or 11N; a bbox across 120 W is refused), takes `--train NAME --train-bbox` for a regional training set, `train --init model.pt --lr` to fine-tune, `detect --context-only`, and prints recall by OSM sport.
- **Downey/Norwalk (LA model, no tuning):** recall 0.82, precision 0.52 vs OSM (40 tennis courts); 12 candidates on no OSM pitch, the 3 in a park/school were a pool, a duplicate of Downey Tennis Center and an unconfirmable school court row. Nothing to add.
- **Elk Grove (Sacramento), zone 10N:** LA model recall 0.27 (tennis 13/34, pickleball 0/14); after fine-tuning on 738 Sacramento chips (4 epochs) recall 0.29 (pickleball 1/14), no real gain. The 2 park/school candidates were a roof and a pool.
- **Verdict:** stop rule hit (fewer than 3 confirmed venues). Not worth scaling: it cannot see pickleball, and tuning does not fix the tennis misses. New courts come from city pages and community reports. Output: `docs/aerial_candidates_downey_norwalk.csv`, `docs/aerial_candidates_elk_grove.csv`.

#### Manual imagery sweep (2026-10-18, Sherman Oaks / Van Nuys area; write-up removed, in git history)
44 views on Esri World Imagery z19 (viewing only): painted court floors are easy to see, walls are not (a 16 ft wall is a 1-2 pixel line), and 5 of the first 12 views were private backyard courts. So no blanket sweep for walls; the cheap routes are the owner's Google Maps sightings (measure on Esri, add a `reported` row), city facility pages, and OSM edits upstream (ADR 0011).

**Update 2026-10-17 (finish of tiers 1-3).** The last 22 uncached non-home pins were queried (16 gave a house-number address, 6 street-only): Nominatim 99 addresses, 439 street-only, 43 over 150 m. `int_venue_address` now also takes the *city* from any cached Nominatim row (street-only and over-150 m rows included; a city never names a street): non-home blank pins with no city fell from 455 to 53, 402 venues gained a city for the map's location search. Venues showing a street: 4,057 of 10,273 (osm 102, Overture place 896, nearest Overture 2,960, Nominatim 99). Still no street: 5,735 home-like by design, 482 non-home (439 street-only, 43 too far). Not done, in order: city for the last ~480 (wider Overture search), parent park/school `addr:*` tags (Overpass re-extract), official-page addresses (phase 2). Roadmap: `CLAUDE.md` item 2.

## Plan: finding venues in the rest of the US with the page reader

Written 2026-11-04. PLAN ONLY: nothing here runs, spends money or edits a seed until the owner says so. It scopes track 1 and track 7 of `docs/ml.md` to one question: how do we find venues in states that have no data layer yet, with the least human reading.

### What the evidence says
- Aerial detection is parked (`docs/articles/the-ml-pilot-i-killed.md`): ~2 new sites per city, pickleball invisible. Not the route.
- Overture and OSM give the net-court skeleton for any state (`docs/new_region_checklist.md`, section 1). The cost per state is section 2, the hand research: city parks and rec, clubs, YMCAs, campuses, walls, events, groups.
- That research is reading public pages. The reader (`ingestion/page_reader.py`, `--engine claude`, quote check, spend cap) already does the reading part. 49 pages have been read so far (`docs/reader_pilot_results.csv`).
- **The gap is finding pages, not reading them.** In the current build only 921 of 9,720 CA venues and 129 of 547 NV venues carry a website (measured 2026-11-04 from `marts.mart_venue_finder`, about 9% and 24%). The reader's pilot input (hand-settled `manual_venues.csv` rows) does not exist for a new state.

### Pilot (one state, chosen by the owner)
1. **URL source, free and public.** Start from each Census place in the state (`data/raw/census_boundaries.csv` already holds places). For the city's official site use Wikidata's "official website" property for the place (public, no key, untested here: measure how many places have one before relying on it). From that site fetch only the parks and recreation pages one hop away (robots.txt respected, project User-Agent, one request per host every few seconds, as the reader already does). Add the state sections of the national bodies (USTA, USA Pickleball, USA Padel and the others in `docs/event_group_search.md`) as a second list.
2. **Read.** `page_reader.py --input urls.csv --engine claude`, dry run first to print pages and the token estimate. Facts stay `inferred` in `docs/reader_candidates.csv`; nothing reaches seeds. A person promotes a candidate into `manual_venues.csv` / `venue_actions.csv` with its evidence, as for every other source.
3. **Order the work with the gap mart.** Rank places by `mart_market_gaps`-style gaps, adding Census population (no key) so a big city with no listed courts is read before a hamlet. Rule-based sort first; a model only if the sort measurably misses.
4. **Measure before scaling.** Hold out 30 pages nobody tuned on. Report per field (sport, courts, setting, access, address, booking link) precision, recall and no-quote share for rules vs the Claude engine, with intervals (`docs/ml.md`, section 6). Stop rule, written now: if fewer than 10 candidates per 100 pages read survive review as new venues or new link-outs, do not scale; fall back to hand search for that state.

### Cost and limits
- Cheapest first: the free rules engine on every page, the Claude engine only on pages the rules read as sport-relevant but incomplete. Weekly cap per ADR 0019 and the $20 a month ceiling; the dry run gives the real estimate, so quote no price until it has run.
- Pages that block bots stay hand review. Home-like pins never get an inferred street. Operator is not venue.
- Honest label: reader output is "inferred, read from the page", never "confirmed" (ADR 0007, 0017).

### Decisions needed from the owner
1. Which state is the pilot (it should already be queued for CA parity under ADR 0028).
2. OK to spend up to a stated cap on the Claude engine for the held-out comparison.
3. OK to fetch city sites one hop deep (new behaviour for the reader; today it reads listed URLs only).

### Not in this plan
Learned entity matching, aerial imagery, recommender, partnership data (all parked or off limits per `docs/ml.md` and CLAUDE.md).
