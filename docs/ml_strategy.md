# ML and agents strategy: how AI takes over the project's work

Written 2026-10-21. A plan, not a decision: nothing here starts a scheduled task, spends money or changes a rule until the owner says so (CLAUDE.md, ADR 0019). It sits above three existing documents and does not replace them:
`docs/ml_plan.md` (the ML phases and their results), `docs/self_service_plan.md` (which refresh steps a machine can own) and ADR 0017 / 0019 (the page reader, and when an agent may merge). Read those for detail; this page is the order, the architecture and the case for doing it.

## 1. The case for ML here (the short version)
CourtConnect is a data-quality problem on messy open data, run by one person. Three facts make ML a good fit, and each one is already measured in this repo:

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

## 2. The honest answer to "should we build agents, or is there another way?"
Yes, build agents, but not one free-roaming agent. There are three ways to automate this project, and the right answer is the middle one, built on top of the first.

| Approach | What it is | Fits CourtConnect? |
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

## 3. Principles (carried over from the ADRs, plus three new ones)
- Model proposes, code decides. A model never merges (ADR 0019 section 1).
- Every fact carries an exact quote and a URL that code, not the model, found on the fetched page (ADR 0017).
- Honest labelling: where no person reviewed a fact the map says "checked automatically; a person audits a sample", never "reviewed" (ADR 0019 section 7).
- Public pages only, no owner logins, no Google Places data, project User-Agent only, no personal data, links out only.
- Cheapest engine that clears the bar: free rules, then a small Claude model, then bigger only if a measured gap needs it (bare-minimum budget; $20 a month cap).
- **New: a model ships only if it beats a stated baseline on a held-out set**, with the interval reported (see section 6). No "it looked right on the pages I tuned it on" (the rules engine's current numbers are tuned on the pages they are measured on, and the notes already say so).
- **New: start the track-record clock early.** ADR 0019 makes auto-merge depend on N clean PRs (R0: 6, about 3 months; R1: 15; R2: 30 per field type). Engineering is not the slow part; the clock is. Every week stage 0 does not run delays autonomy by a week.
- **New: one place to measure.** A monthly `docs/ml_scoreboard.csv` line (section 6) so progress and regressions are numbers, not impressions.

## 4. ML tracks: what, why, priority
Ranked by value to the self-service goal against effort and risk. "Gold" = the labelled set that measures it.

| # | Track | What it does | Gold / baseline | Value | Effort | Verdict |
|---|---|---|---|---|---|---|
| 1 | **Reader** (LLM page reading, ADR 0017) | Turns a venue or facility page into fixed fields with quotes: sports, courts per sport, indoor/outdoor, access, street address, booking link | 34 hand-settled pages; rules engine as the baseline | Very high: unlocks R2, the review queue, scans, leads, non-home addresses | Medium (script exists, needs the model engine + cap) | **Do first** |
| 2 | **Feedback triage** | Classifies and dedupes issues, form reports and beta feedback; extracts the proposed row; screens for spam and injection; drafts the reply or the seed edit | Past issues + form rows, hand-labelled once | Very high: replaces the `approved` label, the main human gate | Medium | **Do second** |
| 3 | **Priority ranker, widened** | Today ranks the review queue. Extend to "what should the agents read or recheck next": stale venues, leads, unverified fields; calibrate its probabilities | 173 override rows; leave-one-out | High, cheap: makes every agent spend its budget well | Low | **Do alongside 1** |
| 4 | **Extract drift / anomaly guard** | Flags an extract or build that looks wrong before it ships: per-sport and per-area count shifts, a new Overture release, sudden address-fill changes, test-set drift | Backtest on past extracts (trend CSV, snapshots) | High: this is what lets R0 refreshes auto-merge safely | Low | **Do before R0 goes live** |
| 5 | **Watcher** (page-change and closure signals) | Detects a venue page that changed, went dead, or says "permanently closed" / "coming soon" / "now open"; rechecks leads and events | `closed_places.csv`, lead outcomes, padel rechecks | Medium-high: covers rechecks (item 4, 8 on the roadmap) | Medium | After 1 |
| 6 | **Learned matcher** (Overture/OSM entity resolution) | A gradient-boosted pair classifier as a challenger to the hand rules | Match gold set (129 pairs, 0 wrong, 4 missed) | Low now: rules leave little room; the gold set is also small | Medium | **Shadow only.** Adopt only if it beats the rules on a fresh sample without a wrong merge |
| 7 | **Supply-gap and demand view** (`mart_supply_gap`) | Courts per 10,000 residents by sport and area (Census, no key) plus anonymous click signals | Needs beta traffic (GoatCounter) | Medium, product-facing: a story for the beta and for "discover new sports" | Medium | After beta data exists; ADR first (privacy line in `ml_plan.md`) |
| 8 | **"Try something new" recommender** (DROPPED 2026-10-21, ADR 0015 amendment) | Suggests sports like the ones you play, using `ref_sport_fit` and `sport_also_played`; no accounts, no tracking | Hand check on 10 sport pairs; click-through in beta | Medium, directly serves the mission (ADR 0015) | Low | After beta; a similarity table, not a deep model |
| 9 | **Aerial court detector** (phase 3) | Finds courts in no dataset | OSM pitches | Low: single-digit new sites per city, mostly private, needs a person per site | High | **Parked.** Revisit only after 1-5, with fine-tuning and recall by sport |

Notes on the table:
- **Tracks 1 and 3 reinforce each other.** The ranker picks which pages the reader reads first; the reader's accepted facts become new ranker labels. That is the flywheel in one loop.
- **Track 4 is the quiet enabler.** ADR 0019 gates cover a build that fails; they do not cover a build that passes and is wrong (for example an Overture release that silently drops a category). A drift check closes that hole and is cheap statistics, not deep learning.
- **Track 6 is deliberately low.** It is the most "ML-looking" idea and the least useful today. Say so out loud so effort goes where the measured gap is.
- **Local open model** (free middle path in `docs/sessions/2026-10-18-page-reader-pilot.md`): try it for track 1 only if the paid engine's cost or the cap becomes the limit. Same `verify()`, same quote check.

### Track 1 in detail: the reader roadmap
1. **Freeze the reader gold set.** The 34 hand-settled pages, plus 30 fresh ones nobody tuned on (held out for good). Record per field: expected value or "not on page".
2. **Add the model engine** (`--engine claude`), same fixed fields, same quote check. Dry run prints pages and tokens first; abort if the estimate exceeds the remaining weekly cap (ADR 0019 numbers). Cache by URL + date.
3. **Compare three engines on the held-out pages:** rules, small Claude model, (optional) local model. Report field precision, recall, and no-quote share, per field type (sport, courts, setting, access, address, booking link).
4. **Decide per field, not per engine.** Sport and setting may clear the bar with rules alone; access and address may need the model. Each field type earns its own class (ADR 0019 R2, per field type).
5. **Wire it to targets:** the review queue first (116 rows), then `*-access` leads, club-named venues, the 482 non-home pins without a street (ADR 0016 and the home-privacy rule still apply: home-like pins never get an inferred street), then city rec directories.
6. **Pages the reader can't reach** (3 of 20 block bots; robots.txt is respected) stay hand review. Don't engineer around them.

### Track 2 in detail: the triage agent
- Inputs: `venue-change` issues, the community form sheet (`make sync-reports`), and later beta feedback.
- Steps: classify (change request / bug / feature idea / duplicate / spam / looks like prompt injection) -> if a change request, fetch the cited public page with the reader and quote-check the claim -> propose the seed row or ask the reporter exactly what is missing -> post the draft; stage 0 means a person still adds `approved`.
- Untrusted input: issue text is data. The classifier has no tools, returns a fixed label and fields, and can't act on instructions inside the issue (ADR 0019 section 6).
- Gold: label every past issue and form row once (a short session), hold some out, measure class accuracy and the share of drafted rows the owner edits.
- Beta use: the same agent groups beta feedback into themes and drafts the RICE table (`docs/feedback_findings.md`), so the owner reads a summary, not 40 messages.

## 5. Agent roster
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

## 6. Evaluation and the ML scoreboard
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

## 7. Where agents run (the open question in ADR 0019)
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

## 8. Roadmap
Phases use order and exit tests, not dates: the beta dates are still TBD (December in `CLAUDE.md`, 2026-11-02 in `ml_plan.md`). One task per session, as the project rules say.

### Phase 0: groundwork, no spend, nothing scheduled (now)
Each item is a small PR or a single session.
1. `docs/agent_log.csv` (columns: date, agent, class, pr, outcome = unchanged / edited / rejected / reverted) and a README paragraph on how to fill it.
2. Merge gate script in **shadow mode** (computes "would auto-merge" for a PR, posts nothing). Includes the path allowlist per class and the diff caps from ADR 0019.
3. **Drift check** (track 4): a script that compares a new extract and build against the last N, fails loudly on a shift beyond a stated threshold, added to the refresh runbook before step 8.
4. **Reader gold set** frozen (track 1 step 1) and **triage gold set**: label past issues and form rows.
5. Start measuring `owner_review_min` and `docs/ml_scoreboard.csv` with what exists (ranker, match, scorecard).
6. Move the CLAUDE.md "Current status" lines into the scoreboard / trend CSV, as `self_service_plan.md` already suggests, so agents don't edit a shared file.

**Exit:** a shadow gate verdict can be produced for any PR; the scoreboard has its first line; both gold sets exist.

### Phase 1: reader and triage pilots (needs the owner's key and cap)
1. Owner sets the API key in `.env` and confirms the cap ($20 a month, $5 a week per ADR 0019) and the precision bar.
2. Reader Claude engine pilot on the held-out pages (track 1 steps 2-4). Write the result into `docs/models/reader.md`.
3. Triage agent in draft mode on live issues: it comments or drafts; a person still labels `approved`. Log every outcome.
4. Widen the ranker (track 3) to rank reader targets; retrain after each accepted batch.

**Exit:** field precision (with interval) per field type; triage draft accepted unchanged on at least 70% of change-request issues (suggested); cost per accepted fact known.

### Phase 2: draft-mode agents on a schedule, shadow gate on (beta window)
1. Owner approves a schedule (nothing starts without it). `refresh` agent runs the runbook and opens the PR; a person merges (stage 0).
2. Reader works the review queue, `*-access` leads and club-named venues; every fact is a PR or a candidate row with a quote.
3. Triage handles beta feedback and issues; the synthesizer produces the RICE draft.
4. Shadow merge gate runs on every agent PR; compare its verdicts with the owner's merges.
5. Weekly auditor digest begins, sampling the PRs.

**Exit:** at least 6 refresh PRs in the log; zero gate false negatives in shadow; the owner's review time is down against Phase 0's baseline.

### Phase 3: promote what has earned it (earliest around Q1 2027)
1. R0 and R1 switch to auto-merge only when their ADR 0019 numbers are met and the owner switches them on. R0 needs 6 clean PRs plus 3 shadow runs, so about three months of stage 0 first.
2. R2 per field type: only fields whose precision and interval clear the bar.
3. Watcher agent live (closures stay R3; the page must state the closure).
4. Product: supply-gap view, using beta data (each behind an ADR where it touches privacy).
5. Learned matcher as a shadow challenger on the next gold sample; adopt only on a clear win.

### Later (each needs its own ADR first)
Link discovery beyond held URLs; PDFs and images (directory sites that forbid reuse stay off limits regardless); a local open model for the reader; a read-only MCP server over `venues.json`; aerial v2 with fine-tuning; moving to the `courtconnect` repo name; moving `data/raw` to object storage.

## 9. Budget
- **Cap:** $20 a month, $5 a week (ADR 0019). A dry run aborts if its estimate exceeds the week's remainder.
- **Scale:** the 16-page rules pilot was about 28,500 input tokens, so a pilot of that size is cents. A 1,000-page sweep is on the order of 1.8 million input tokens; price it against the current rates for the chosen model before running (rates change, so this page does not quote them).
- **Spend order, cheapest first:** rules (free) -> cached model reads of pages that rules couldn't settle -> second-model check only on facts that would otherwise be applied -> the weekly audit sample. Pages are cached by URL + date, so a page is read once.
- **Free first:** scikit-learn, DuckDB, Census boundaries, Planetary Computer and OSM stay the default. Paid APIs are optional and capped (project budget rule).

## 10. Risks and how the plan answers them
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

## 11. Decisions needed from the owner
1. **Approve Phase 0** (no spend, nothing scheduled). This is the only decision needed to start.
2. API key and cap for Phase 1; the reader precision bar, and whether to add the "lower bound above 90%" rule.
3. When agents may be scheduled (Phase 2), and whether the first runner is local.
4. Whether to write the two ADRs this plan implies: **ADR 0022 ML evaluation standard** (held-out sets, intervals, model cards, scoreboard) and **ADR 0023 agent runtime** (where agents run, post-merge export job, raw data in object storage). Both are drafts for the owner to accept, like ADR 0019.
5. Which review-time goal to aim for. Suggested: measure two months first, then set a target (for example under an hour a month of routine review by the end of Phase 3, escalations excluded).

## 12. What to do first
Start Phase 0 item 1, 2 and 4 (the log, the shadow gate, the two gold sets). They cost no money, need no schedule, and are the prerequisites for every later step: without the gold sets there's nothing to measure a model against, and without the log the track-record clock never starts.
