# Self-service plan: which refresh steps a machine can own

Goal (ADR 0015, long-term): the project runs itself with as little human review as possible. Rules for when an agent may merge on its own are in ADR 0019. This page is step 1 of that plan: classify every step of `docs/monthly_refresh.md` and say what blocks automating it. Written 2026-10-18; nothing is automated yet.

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

Outside the runbook but on the "Open, in order" list:
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
