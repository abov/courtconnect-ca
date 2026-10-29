# Feedback findings (friends beta)

Plan and method: `docs/feedback_round.md`. Fill in when the round starts.

Round: start ____, end ____. GoatCounter own-IP excluded since ____.
Baseline (scorecard run locally 2026-10-29 via `make quality`; not committed because the CI no-regression gate rejects it until the refresh clears the breaches): venues 10,279, named 16.1% (target 25%, breach), upcoming events 71. Known SLA breaches at baseline: Overture places last seen 2026-09-23 (97.1% of venues fresh vs 99%), oldest event check 17 days (14 allowed); 5 of 8 service levels met.

## Log
| Date | Who (sport, area) | Type | What happened | Sev (1-3) | Source | Status / PR |
|---|---|---|---|---|---|---|

Type: bug / missing place / wrong data / confusing label / feature idea / pricing. Source: call / message / analytics.

## RICE (score = Reach x Impact x Confidence / Effort)
Reach = people hit (of N). Impact: 3 big, 2 medium, 1 small, 0.5 minimal. Confidence: 100 / 80 / 50 %. Effort: person-days.

| Theme | Reach | Impact | Conf. | Effort | Score | Decision |
|---|---|---|---|---|---|---|

Top three go into "Open, in order" in `CLAUDE.md`.

## Numbers (GoatCounter, directional only)
| Measure | Result | Target |
|---|---|---|
| Invitees opening 2+ times | | most |
| `linkout` / `venue-open` | | 25%+ |
| Suggestions (`suggest-change` + `report-form` + `osm-edit`) | | 3+ |

## Decision
Stay personal / open source / paid layer: ____ (ADR if direction changes).
