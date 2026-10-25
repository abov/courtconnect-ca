# Plan: "If you like X, try Y" sport suggestions

Status: PLAN ONLY (2026-10-25), nothing built. Owner idea; brings back the "Try something new" recommender dropped 2026-10-21 (`docs/ml_strategy.md` row 8, ADR 0015), now with a concrete trigger. Rank with beta findings (December).

## Goal
When someone keeps looking at one sport, offer one related sport they might enjoy, in a way that is light, optional and fun. Serves the mission (ADR 0015: try a new sport). Not a retention trick: no accounts, no streaks, no reminders (same stance as the focus helpers in `app/index.html`).

## 1. How we know someone keeps coming back to one sport
Everything stays in the browser (the existing `store` in `localStorage`, try/catch, `cc.` prefix). Nothing is sent anywhere, no ID.
- Keep a tiny counter `cc.sportSeen = {sport: {n, days[]}}`: bump `n` when a sport is picked, a pin of that sport is opened, or a link-out is clicked with that sport active (these are the events GoatCounter already counts).
- "Consistent" = same sport on **3 different days**, or **5 actions in one visit** with no other sport picked. Count distinct days, so one long session does not trigger twice.
- Trigger once per sport: remember `cc.suggested = {sport: date}`; never show again for that sport for 60 days; "Not interested" ends it for good.
- Learning that someone is "a pickleball person" is inferred from behaviour; the card says so ("Since you've been looking at Pickleball...").

## 2. What we suggest (the engine)
No ML. A small hand-curated table plus existing data:
- `transform/seeds/sport_related.csv`: `sport, suggest, reason, effort` (e.g. Pickleball -> Padel, "Same court-sized game with walls and a bounce off the glass"; Tennis -> Padel / Pickleball). Reasons are written by us (owner reviews), one line each, source or `inferred` label.
- Seed from data we already have: `sport_also_played.csv` (played on the same courts) and `ref_sport_fit` (court fits inside the host court). These say "you can try it on a court you already know".
- Candidate must be **playable near the person**: suggest only sports with at least one venue in the current map view or the searched city (or the nearest one, with distance). Never suggest a sport with nothing nearby unless labelled "none listed yet".
- Rank: (1) same court type, so easy to start; (2) has a "try it" link-out or beginner-friendly note; (3) nearer. Show **one** suggestion, not a list.

## 3. What it looks like (options, cheapest first)
| Option | Feel | Cost | Risk |
|---|---|---|---|
| A. Inline card in the existing "About <sport>" card: "Like Pickleball? Try Padel, 2 miles away" + [Show me] | Calm, in context, no interruption | Lowest | Missed by people who do not open About |
| B. One-time dismissible banner under the sport dropdown after the trigger | Noticeable, friendly | Low | Slightly pushy if it repeats |
| C. Empty-state suggestion: when a pick has no venues nearby, "Nothing for X here yet. People who like X also try Y" | Helpful at a dead end | Low | Only fires on misses |
| D. Pop-up modal | Interruptive on a phone map | Low | Annoying; **no** |
| E. Email | Needs identity and a provider | High | Conflicts with ADR 0025 until it ships; **no**, revisit inside the favorites digest ("a new sport near you") |

**Recommended: A + C first, B after.** All three share one card component: sport icon, one line of reason, [Show me] (switches the filter and logs `event/suggest-accept/<from>-<to>`), [Not now]. No modal, nothing sideways, works at 375/320 px, dark mode via existing tokens. Fun touch: a "Court twin" label where the courts are literally the same size ("Same court, new game").

## 4. Measuring it (GoatCounter, anonymous)
New events: `event/suggest-shown/<from>-<to>`, `suggest-accept/...`, `suggest-dismiss/...`. Success = accept rate and whether accepted suggestions lead to `linkout-sport/<to>`. Drop a pair if shown 20+ times with no accepts.

## 5. Decide with the beta
Ask in `docs/feedback_round.md`: "Would you like a nudge to try a similar sport?" and "Where would you expect it?" before building. Check demand with `make usage` first: how many visitors pick the same sport on 3+ days (needs a few weeks of traffic; today there is none to measure).

## Order of work (small PRs, one per session)
1. `sport_related.csv` seed + tests (not_null, both sports exist in the sheet, suggest != sport) + export key; 10-pair hand check.
2. Card component (A + C) in the app, trigger logic with the local counter, events.
3. Banner (B) only if A/C show low pickup.
4. Review accept rates after 4 weeks; prune pairs.

## Open questions for the owner
- OK that "consistent" is local-only and approximate (clearing the browser resets it)?
- Who writes the reasons for the first ~15 pairs: Claude drafts, owner approves?
- Email variant: fold into ADR 0025 later, or leave out?
