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

## 2. What we suggest (the engine): relevance first
Rule of thumb: **a missing suggestion beats a poor one.** If no candidate passes every gate below, show nothing.
No ML. A small hand-curated table plus existing data:
- `transform/seeds/sport_related.csv`: `sport, suggest, reason, effort` (e.g. Pickleball -> Padel, "Same court-sized game with walls and a bounce off the glass"; Tennis -> Padel / Pickleball). Reasons are written by us (owner reviews), one line each, source or `inferred` label. Only pairs a person would plausibly enjoy because of a real link: same racket or equipment family, skills that carry over, similar pace or format (singles/doubles, wall play), or the same court.
- Seed from data we already have: `sport_also_played.csv` (played on the same courts) and `ref_sport_fit` (court fits inside the host court). These say "you can try it on a court you already know".
- **Gates (all must pass):**
  1. The pair is in the curated table (no popularity-only or random picks).
  2. Not a sport they already picked or opened (their counter says they know it).
  3. **Startable near them:** a venue in the current view or searched city, ideally with a way in (lesson, clinic, group class, open play or drop-in link-out; the seed has ~37 of these). Otherwise skip, or show the nearest with distance.
  4. Fits their active filters: if they filter to Free, indoor or public-access, suggest only sports that have such a venue. Members-only or private venues never count as "try it".
  5. Inferred availability is labelled inferred ("courts that can be lined for it"), never confirmed.
- Rank the survivors: (1) strongest reason (same court > same equipment > similar feel); (2) has a beginner way in; (3) nearer. Show **one** suggestion, not a list.
- Hand check before launch: for each pair, would a regular player of the first sport say "yes, that makes sense"? Drop the pair if not.

## 3. What it looks like (options, cheapest first)
| Option | Feel | Cost | Risk |
|---|---|---|---|
| A. Inline card in the existing "About <sport>" card: "Like Pickleball? Try Padel, 2 miles away" + [Show me] | Calm, in context, no interruption | Lowest | Missed by people who do not open About |
| B. One-time dismissible banner under the sport dropdown after the trigger | Noticeable, friendly | Low | Slightly pushy if it repeats |
| C. Empty-state suggestion: when a pick has no venues nearby, "Nothing for X here yet. People who like X also try Y" | Helpful at a dead end | Low | Only fires on misses |
| D. Pop-up modal | Interruptive on a phone map | Low | Annoying; **no** |
| E. Email | Needs identity and a provider | High | Conflicts with ADR 0025 until it ships; **no**, revisit inside the favorites digest ("a new sport near you") |

**Recommended: A + C first, B after.** All three share one card component: sport icon, one line of reason, [Show me] (switches the filter and logs `event/suggest-accept/<from>-<to>`), [Not now]. No modal, nothing sideways, works at 375/320 px, dark mode via existing tokens. Fun touch: a "Court twin" label where the courts are literally the same size ("Same court, new game").

## 4. If they say yes: a "Get started with <sport>" path
[Show me] does not just switch the filter; it opens a short guide so the person can actually begin. Same card style as "About <sport>", four steps, each shown only when we have real data:
1. **What it is:** our one-line blurb (sheet `Blurb`) and how it differs from the sport they know ("Like pickleball, but you can play off the walls").
2. **Try it near you:** the nearest venue with a beginner way in, as link-outs: lesson, clinic, group class, open play or drop-in (existing `venue_actions` types), with price if known. No such venue: nearest court plus "ask the venue about beginners".
3. **Rent or buy gear:** what you need (sheet `base_gear`) and where. "Rent at the venue" only when a public venue page says so: needs a new `rental` action type (or a flag) in `venue_actions.csv` with `evidence` + `verified_on`, as for every link-out. "Buy": the sheet's `Gear URL`, a neutral buying guide or the official body, never a store we pick for pay. If unknown, say "Most clubs lend rackets; ask when you book" only if a source supports it, otherwise omit.
4. **Shops and places to ask, near you:** see "Gear shops near the last search" below.
5. **Learn more:** a beginner guide or the sport's official body (the sheet's `Learn URL`, `Rules URL`, `Court URL`, `Gear URL`). A guide or governing-body page is as good as a shop link, and is the fallback wherever we have no sourced rental or shop.
CourtConnect still links out and takes no bookings or payments, and no affiliate links. Any row we cannot source is hidden, not guessed. The guide also opens from the sport's About card, so anyone can use it without being nudged.

### Gear shops near the last search
Show up to 3 places to ask about, rent or buy gear, closest to where the person last searched (the city, zip or map centre they used, kept only in their browser as `cc.lastArea`; nothing sent anywhere, no "use my location" needed).
- **Ranked:** (1) the nearest venue's own pro shop or front desk when a public page says it rents or sells (e.g. a tennis pro shop), (2) a sport-specific store (padel, pickleball, racquet-sport specialists), (3) a general sporting-goods store, labelled "may not stock <sport>".
- **Data (no Google Places, ADR 0005):** Overture places (category sporting goods) and OSM `shop=sports` / `shop=sports` + `sport=*` tags, loaded as a new raw table and a small mart `mart_gear_shops` (name, lat/lon, city, source, `sport_tag` when tagged). Sport-specific stores and rental places are confirmed by hand in a seed `gear_shops.csv` (`name, sport, kind rent|buy|both, url, evidence, verified_on`), like `venue_actions.csv`. Export a compact key, only shops within reach of a mapped venue, to keep `venues.json` small.
- **Honest labels:** "Sporting goods store" is inferred, not "sells padel rackets". Only sport-tagged or hand-confirmed shops get the sport name. Show distance from the searched area; hide a shop whose listing looks closed. We link out and take no bookings or payments; no affiliate links.
- **Fallbacks:** no shop within ~25 miles: show the venue's "ask about rentals" line and the guide/official body link only. Never show an empty box.
- Open question: Overture's coverage of small specialist shops is thin, so expect the hand-confirmed seed to carry the sports that matter most (padel, pickleball, squash, badminton). Measure how many mapped metros have at least one confirmed shop before building the UI.

## 5. Measuring it (GoatCounter, anonymous)
New events: `event/suggest-shown/<from>-<to>`, `suggest-accept/...`, `suggest-dismiss/...`, plus `event/getstarted-step/<kind>` (lesson, rent, buy, learn) for which step helps. Success = accept rate and whether accepted suggestions lead to a get-started step or `linkout-sport/<to>`. Drop a pair if shown 20+ times with no accepts.

## 6. Decide with the beta
Ask in `docs/feedback_round.md`: "Would you like a nudge to try a similar sport?" and "Where would you expect it?" before building. Check demand with `make usage` first: how many visitors pick the same sport on 3+ days (needs a few weeks of traffic; today there is none to measure).

## Order of work (small PRs, one per session)
1. `sport_related.csv` seed + tests (not_null, both sports exist in the sheet, suggest != sport) + export key; 10-pair hand check.
2. "Get started" guide for mapped sports (step 4 above): add a `rental` action type + evidence, fill `Gear URL` for the first sports; useful on its own.
2b. Gear shops: extract Overture/OSM shops, `mart_gear_shops`, hand-confirmed `gear_shops.csv` for padel/pickleball/tennis first, then the "near your last search" list in the guide.
3. Suggestion card (A + C) in the app, relevance gates, trigger logic with the local counter, events.
4. Banner (B) only if A/C show low pickup.
5. Review accept rates after 4 weeks; prune pairs.

## Open questions for the owner
- OK that "consistent" is local-only and approximate (clearing the browser resets it)?
- Who writes the reasons for the first ~15 pairs: Claude drafts, owner approves?
- Email variant: fold into ADR 0025 later, or leave out?
