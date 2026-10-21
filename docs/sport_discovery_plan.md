# Plan: every sport in the dropdown + "what is this sport?" details

Status: PLAN ONLY (2026-10-16), nothing built. Starts after the beta findings (10-29..11-01); ranks with roadmap item 7c and ADR 0015 (7b, tennis visibility + "Try something new", dropped 2026-10-21) (mission: discover sports beyond pickleball).
Source of truth for sports: the Google Sheet (synced into `transform/seeds/all_racquet.csv` by `make sync-sports`; never hand-edit the seed).

## Problem (measured 2026-10-16 from `app/data/venues.json`)
- 76 sports in the sheet; the dropdown (`populateSports()` in `app/index.html`) lists a sport only if it has venues (`s.v > 0`), a play-anywhere note (`s.w`) or known walls. **55 sports are hidden** because they have zero venues: e.g. Crossminton, Real Tennis, Jai alai, Soft Tennis, Teqis, Touchtennis, Road Tennis, Kadima, Frescoball, Jokari, Ricochet, Racket Hockey, Micro Pickleball, Hand Tennis.
- Several visible "sports" are only inferred from tennis/pickleball courts (Frescotennis, Loboton, Tennis Triples = 8,086 venues; Lite Tennis, Skyball, Spec Tennis, Typti = 920). Those counts must be labelled inferred, not confirmed.
- Someone who does not know a sport gets no explanation of what it is, what gear it needs, or where it is played.

## Part 1: show all sports in the dropdown
Cheapest honest version, no new venue data needed:
1. Dropdown lists all 76 sports alphabetically; sports with zero venues are greyed out and marked "no places yet" (decided 2026-10-16); keep the existing counts rule (counts follow the filters).
2. Picking a not-mapped sport shows an empty-state card instead of a blank map: "No place for X is listed in CA or NV yet", the sport details (Part 2), the closest sport that *is* mapped when one exists (via `sport_also_played.csv`, e.g. Micro Pickleball -> Pickleball), and a "Know a place? Suggest it" button that reuses the suggest-a-change form pre-filled with the sport.
3. Play-anywhere sports (`sport_play_anywhere.csv`) keep their note.
4. Map keeps showing nothing for them; never fake pins. The coverage dialog already lists status per sport (`covered`, `sparse`, `possible_only`, `tagged_none_found`, `not_found`).
5. Search the web for real places for the not-mapped sports, in this order (cheapest first, one family per session): wall/handball family (Jokari, Paleta, Frontenis, Xare, Jai alai), Soft Tennis / Touchtennis / Real Tennis (clubs and federations list venues), Crossminton and Tamburello (federation club finders), then the long tail of one-off rec sports (most likely stay "not mapped": say so). Confirmed finds go in `manual_venues.csv` (with `confirmation` + evidence), as for every other sport.
6. Add a check: `ci/` test that every sheet sport appears in the export `sports` list (so a new sheet row can never silently vanish) and that every one has a details row (Part 2).

## Part 2: sport details under the dropdown
When a sport is selected, a small collapsible card under the dropdown ("About Padel"):
- **One-sentence blurb** (what it is, e.g. "Doubles racket sport played in a glass-walled court, a mix of tennis and squash").
- **Quick facts** from sheet columns we already store: players (`players`), court size (`court_dim`) and surface (`court_surface`), net height (`net_ht`), gear (`base_gear`), governing body (`org`) and origin year (`year_origin`), popularity class.
- **Can I try it near me?** line from our own data: "N venues listed, X confirmed" or "none listed yet". Inferred sports say "inferred from tennis courts".
- **Learn more** link: the sheet's `url` (official body) plus a Wikipedia link where an article exists. Link out only; do not copy Wikipedia text (copyright and honesty: our own one-liner, their page for depth).
- **Beginner tip** (optional, one line): equipment you can rent, whether lessons are common, typical pace. Only when we can state it from a public source.

Data:
- New seed `transform/seeds/sport_details.csv`: `sport, blurb, wiki_url, beginner_tip, verified_on, source`. The sheet stays the source for the numeric facts; this seed holds only what the sheet lacks. (Option: add `blurb`/`wiki_url` columns to the sheet itself and sync, so the sheet stays the single source; decide when starting. Recommended: sheet columns, because the sheet must stay in sync with the project anyway.)
- Export into `venues.json` `sports[]` as short keys (`d` blurb, `f` facts, `u` links) to keep the file small; app renders with `textContent`, links `rel="noopener noreferrer"`, https only (same rules as `watch_events.csv`).
- Writing the 76 blurbs: draft from the sheet + Wikipedia/federation pages, mark `verified_on` and `source`; label anything uncertain as such. Do the 21 sports with venues first, then the rest.
- Tests: dbt `not_null` on blurb, `https` regexp on URLs, one row per sport.

UX notes: mobile 375/320px first (card collapsed by default on phones, expanded on desktop); no layout shift in the header; works with the sport icon already beside the dropdown (`updateSportIcon()`); dark mode via existing colour tokens. Eyeball live, since the browser pane refuses localhost.

## Order of work (small PRs, one per session)
1. Seed + sheet columns + export + tests for `sport_details` (21 mapped sports first).
2. Details card in the app for mapped sports.
3. Dropdown shows all 76 (two groups) + empty-state card + suggest-a-place prefill.
4. Blurbs for the remaining 55 sports.
5. Venue searches for not-mapped sports, one family per session (Part 1 step 5).
6. Re-run `pages.yml` after merge; confirm PR MERGED before calling it shipped.

## Decisions (owner, 2026-10-16)

- Blurb and wiki columns live in the Google Sheet (synced by `make sync-sports`), not a repo seed. The `sport_details.csv` seed in Part 2 is dropped.
- Unmapped sports stay in the main list, greyed out and marked "no places yet" (no separate group; supersedes the `<optgroup>` idea in Part 1).
- No popularity-class labels on the card.

## Update (2026-10-18)

- Part 2 built early for the card (not the all-76 dropdown): sheet columns `Blurb`, `Learn URL`, `Rules URL`, `Court URL`, `Gear URL` (owner chose sheet columns and all 76 sports). Draft values for the 27 verifiable sports are in `docs/sport_details_draft.csv`; 49 remain blank. Details: `docs/sessions/2026-10-18-sport-info-card.md`.

## Status (2026-10-21)

- Built: all sheet sports (81) in the dropdown, unmapped ones greyed "(none yet)" with an empty-state line and a pre-filled report-a-venue link (2026-10-19); the "About <sport>" card (2026-10-18).
- Waiting on the owner: the sheet's Blurb / URL columns are still empty, so the card shows facts only. `docs/sport_details_draft.csv` has 63 drafted blurbs to paste in.
- Not started: blurbs for the remaining sports, the CI check (Part 1 step 6), the closest-mapped-sport hint (Part 1 step 2), venue searches (Part 1 step 5).
