# Self-service plan: which refresh steps a machine can own

Goal (ADR 0015, long-term): the project runs itself with as little human review as possible. Rules for when an agent may merge on its own are in ADR 0019. This page is step 1 of that plan: classify every step of `docs/monthly_refresh.md` and say what blocks automating it. Written 2026-10-18; the section "Update 2026-11-17" at the end says what changed since and what is left.

## Classes
| Class | Meaning | Agent may |
|---|---|---|
| **M** mechanical | Same command, pass/fail result, no judgment | run and open a PR; auto-merge once ADR 0019 lets this class |
| **E** evidence | Needs a page read; the answer is a fact with a quote or a date | propose with quote + URL; auto-merge only after the class earns it (ADR 0019 track record) |
| **J** judgment | A choice about scope, risk, money or what the project says | draft only; the owner decides |

## Runbook steps
| # | Step | Class | What a machine does | What blocks full automation |
|---|---|---|---|---|
| 1 | Branch from main, note last scorecard line | M | create `claude/monthly-YYYY-MM`, read `docs/data_quality_trend.csv` | nothing |
| 2 | Sync sports sheet (`make sync-sports`) | M | run the sync, regenerate `osm_sport_map.csv` / `sport_search_terms.csv` | needs read access to the Google Sheet (a secret the runner must hold) |
| 2 | Carry a renamed/new sport through counts and names | E | update `EXPECTED_SPORTS`, `expected_racket_sports`, seeds, scripts; `dbt build` proves the counts | the build catches a miss in the counts, but not every place that names a sport (`manual_walls.csv`, `sport_also_played.csv`, generators): add a check that greps them |
| 2 | Add a new sport to the sheet | J | draft the row | owner owns the sheet; mission/scope choice |
| 2b | Issues: list gaps, duplicates, waiting >14 days | M | `make issues` (read-only) | nothing |
| 2b | Issues: draft the seed row with evidence, ask reporters for missing info | E | triage agent reads the issue + cited page, proposes the row or posts the question | today a human adds the `approved` label (`issue-to-pr.yml`); this is the main human gate to replace. Issue text is untrusted input |
| 2b | Issues: close when the PR merged | M | `gh issue close` with a link | script is read-only on purpose; give the agent comment/close rights only |
| 3 | Extract OSM + Overture (~15 min), addresses, walls | M | run the extract scripts | owner approval today is cost/time control: replace with a time and spend budget. Raw CSVs live in the main checkout's `data/raw`, not in CI: the run must happen where that folder is, or the raw store moves (open question, ADR 0019) |
| 3 | City fill when pins have no city | M | `make city-boundaries` | nothing |
| 4 | Load (`make load`) | M | run | has the 10% shrink guard; a refusal is an escalation, not a retry with `--force` |
| 5 | Link checks (`check-links`, `check-websites`) | M | run, collect failures | nothing |
| 5 | Re-date `verified_on` after a re-read | E | re-fetch, find the quote, set the date | needs the page reader (ADR 0017) so there is a quote to store |
| 5 | Dead link or closed place: change `venue_actions` / `closed_places` | E | propose the edit | closing a venue on thin evidence is a J case (ADR 0019 escalation list) |
| 6 | Build (narrow, then full) | M | `dbt build` | nothing; this is the main gate |
| 7 | `make quality`, `make report` | M | run, diff the scorecard against the last line | needs a written no-regression rule (venue count, SLAs, stale share) |
| 7 | Undated hand-added rows: re-date, or turn into a lead | E | re-read source, re-date with quote, else propose a lead | "leave stale" vs "make a lead" is a small judgment: default to leave stale |
| 8 | Export (`make app-data`), commit `venues.json` | M | run; `ci/check_export_fresh.py` already checks it | `venues.json` collides between PRs: one refresh PR at a time, agents rebase on main and rebuild, never hand-resolve |
| 9 | Commit, PR, confirm merged and the `pages.yml` run | M | open PR, merge when gates pass, confirm the Pages run (it starts by itself) | needs auto-merge on required checks instead of `--admin` |
| 9 | Add 2 lines to CLAUDE.md "Current status" | M | write the numbers | shared file, conflict-prone: move the log to a generated file (e.g. a new line in `docs/data_quality_trend.csv`) and drop the CLAUDE.md edit |

Outside the runbook but on the "Open, in order" list in `docs/status.md`:
| Work | Class | Note |
|---|---|---|
| Gold-set rules, match tuning (item 5) | J | changes how venues merge; needs the eval (`make eval-match`) as a gate before it could be E |
| Facility scans, club-named passes (6, 7) | E | the page reader (ADR 0017) is the enabler |
| Padel / coming-soon lead rechecks (4) | E | official page + quote promotes a lead; opening a venue also updates courts/address |
| Review queue (116 rows) | E | same: reader + quote check |
| Tournament events (`docs/tournament_refresh.md`) | E | separate bi-weekly runbook; classify it next |
| Cost tier, sport cards, UX polish | J | product choices |
| ADRs, mission, privacy, new data sources | J | never autonomous |

## What this tells us
- **About two thirds of the steps are M.** They already have a pass/fail result (dbt, CI, the shrink guard, the freshness check), so the gate exists; what is missing is a runner, a budget and auto-merge.
- **The E steps all wait on one piece: the page reader (ADR 0017)** and a stored quote per fact. Build it once and most of the E rows open up.
- **The only J steps left in a refresh** are adding a sport to the sheet, closing a venue on thin evidence, and anything that changes the rules. Those are the escalations.
- **Gaps to fix first (cheap):** a scorecard no-regression check as a script, a check that every sport name matches the sheet, the CLAUDE.md status lines moved out of the shared file, and the runbook's Snowflake lines removed (done 2026-10-21, ADR 0018).

## Order
1. Fix the cheap gaps above (small PRs, each human-merged as today).
2. Wrap steps 1, 2, 4-9 into one `refresh` agent in **draft mode**: it opens the PR, a person merges (ADR 0019 stage 0).
3. Build the page reader and the triage agent, also in draft mode; log how often the owner changes the output.
4. Promote classes to auto-merge only by the ADR 0019 rule.

---

# Update 2026-11-17: what still needs a person, and the exception queue

The table above is the 2026-10-18 classification. Since then the chain went live (cloud routines, `docs/cloud_routines.md`), every PR is merged by its own session once `dbt-build` is green (CLAUDE.md, owner 2026-11-16), and the R0 merge gate exists (ADR 0019, `docs/merge_gate_threat_model.md`). So "review every PR" is already gone. What is left is **noticing** that something failed and **making the calls only the owner can make**. The smallest change that turns that into an exception queue is a read-only report over outputs we already write: `make exception-queue` (`python ci/exception_queue.py`; `--no-gh` offline). It prints only exceptions, and "Nothing needs the owner." when there are none.

## Where a person is still in the loop
| Touchpoint | Today | Fix | Status |
|---|---|---|---|
| Noticing a stuck or red PR, a failing SLA, a stopped chain | read GitHub and the scorecard by hand | `make exception-queue` | built (this PR) |
| Owner calls buried in leads and PR bodies ("owner call before pinning") | found by chance | the queue lists open leads that name an owner call and any "needs owner decision" section in open or recently merged PR bodies | built (this PR) |
| Authorizing an extract (cost and time control) | owner says yes each cycle | a time and spend budget instead of a yes; the cloud sandbox cannot reach Overpass, so OSM extracts stay on the owner's machine | proposed, needs owner |
| Refreshing `abov/courtconnect-data` after a local extract | manual gzip, split, push; skipping it broke the cloud build on 2026-11-15 | one script, `ingestion/push_data_bundle.py` (`make push-data`, dry run by default, `--push` to push, refuses files that shrank >10%); the queue warns when the data repo is behind `data/raw` | script done 2026-11-18; the owner runs it after each extract |
| `approved` label on issues, form-report review | person | stays human until the page reader's quote check exists (ADR 0019 section 6) | unchanged |
| Weekly audit digest, "no chain PR in 20 days" alert | digest not built (threat model gap 4); the watchdog covers only "Tournaments" PRs | the queue flags 20 days without a chain PR; a weekly digest is a new scheduled workflow | proposed, needs owner OK |
| A routine's model, cron, enabled flag | claude.ai/code/routines only | cannot be edited from the repo | owner |

## Model tier per routine
The model is chosen at claude.ai/code/routines (the repo cannot read or set it), so this is a recommendation; commit trailers show the chain runs on Sonnet 5.5 today. Rule: the model does the cheapest thing the gates can verify.

| Routine | Work | Tier | Why |
|---|---|---|---|
| Parts 1-2 tournaments | read organizer pages, write event rows | Sonnet 5.5 | wrong dates or venues are public facts; `check_seed_evidence` and `check_r2_events` catch form, not truth |
| Parts 3-4 leads, new courts, social | judge an official page against a press claim; promote or leave | Sonnet 5.5, never lower | the promote-or-not call is the judgment step (class E) |
| Part 5 data refresh | run scripts, read pass/fail gates, write a 4-bullet PR | **Haiku 5.5 trial** | steps are class M and every outcome is a deterministic gate (scorecard regression, diff cap, export fresh, dbt); the model only orchestrates |
| Quarterly search interest | run `make interest`, open the PR | **Haiku 5.5 trial** | script-driven, planning signal only, not shown in the app |
| Interactive sessions | research passes, design | Sonnet 5.5; the largest model only for hard design | CLAUDE.md |

Trial rule: switch one routine, compare two cycles (gates green first time, PR edited by a person, `est_cost_usd` in `docs/agent_log.csv`); revert on the first gate failure caused by the model. The $5/week and $10/month caps do not change.

## Gates an auto-merge needs (session or merge gate)
All must pass; a failure is an exception, never a bypass.
1. `dbt-build` green in CI (models, tests, Elementary) and the other `ci.yml` checks: `check_export_fresh`, `check_docs_hub`, `check_seed_evidence`, `check_sport_names`, `check_regions`, `eval_match_gold --check`.
2. `ci/check_venue_drop.py`: the total, or any region of 50+ venues, drops at most 10% against `origin/main`.
3. `ci/check_scorecard_regression.py --base-ref origin/main` on refresh PRs: venues down at most 1%, "seen in 35 days" not lower, no more failing SLAs, no failing tests. The 35-day freshness SLA and the 14-day oldest-event-check SLA live in that scorecard.
4. `ci/region_parity.py --region XX --strict` for any PR that touches a region's data layer.
5. `ci/check_refresh_diff.py`: path allowlist and diff caps for `claude/refresh-*` PRs (the R0 gate). Tournament and research PRs stay session-merged (class R2).
6. `make check-pages` when a PR re-dates `verified_on`: only pages that changed or vanished get re-read, and a re-date without a read is not allowed (ADR 0017).
7. Rebased on `origin/main` right before the merge; `venues.json` never hand-resolved.

Always an exception, whatever is green: anything on the ADR 0019 R3 list (closing a venue on one source, raising a confirmation level, home-like pins, new sources, edits to ADRs, workflows, models, tests, macros or `ingestion/`).

## Owner decisions list
Reserved to the owner by CLAUDE.md and the ADRs. A session records one as a line under "Needs owner decision" in its PR body, or as a `venue_leads.csv` row whose next step says "owner call"; the queue then surfaces it. Nobody works around these.
- Resorts and hotels with courts, in every state (ADR 0028): case by case, access stated.
- Military bases and other restricted access (Fort Bliss, Davis-Monthan, JBPHH): pin or not.
- New regions and countries (the 2026-11-13 ruling keeps OK, CO and Montana off).
- Any extract, `--force` load, or run that needs the owner's machine or `.env`; scheduled loops, new routines, cron or model changes, spend caps.
- New or renamed sports (the sheet is the owner's), new data sources, anything touching ADRs, `CLAUDE.md`, workflows or merge-gate rules.
- Closing a venue on thin evidence, a confirmation-level rise on one source, anything touching a home-like pin or personal data.
- Partnerships, data licences, outside emails, monetization, Google Places data (closed or deferred).
- Mexico: what to do with the unverified automatic layer (`mx-auto-unverified-overture`).

## Session-size budget
- One task per session; a research pass is one region, or one sport in one region.
- End or hand off around **150k tokens of context** (or about 100 tool calls). Check `get_usage` every ~25 calls; do not wait for 200-300k.
- The hand-off is the PR description (2-4 bullets: what changed, what is not verified, what is next), never a session note or a shared log. Unfinished work becomes a draft PR and a fresh session picks it up.
- A routine that cannot finish lists exactly which sources it did not read (`docs/tournament_run_parts.md`) rather than reading fewer.
- Lightest model tier the gates can check (above); the largest only for design.

## Proposed, not started (each needs the owner's OK)
1. **Done 2026-11-18.** Run `make exception-queue` at the end of Part 5 and paste it into that PR's body (one line in `docs/refresh_agent.md` step 9; no new schedule).
2. A weekly GitHub Action that runs the queue and posts it as one issue (a new scheduled workflow; also covers the digest half of threat-model gap 4).
3. The Haiku 5.5 trial for Part 5 and the quarterly routine.
4. Queue warning **done 2026-11-18** (`ci/exception_queue.py` compares the newest local extract CSV with the data repo's latest commit; skipped silently if `gh` or the repo is unreachable). Data-repo refresh scripted **2026-11-18** (`make push-data`; dry run by default).
5. One branch prefix for refresh PRs (`claude/refresh-*` in the gate vs `claude/monthly-*` in the runbook).
