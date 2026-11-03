# Chatbot plan (draft, 2026-11-02)

Goal: test whether a chatbot is useful to players, and what it needs. Not built yet; ADR 0033 (proposed) holds the decisions. Waits for the December beta before anything is hosted.

## Two layers (owner, 2026-11-02: free first, AI later)
1. **Layer 1, free "ask box":** no AI model, no key, no server. Rules read the sport, city, filters and intent from the question, then search `venues.json` in the browser (`app/ask.js`, test page `app/ask.html`, not linked from the main page yet; checks: `node chatbot/test_ask.js`). Costs nothing per message. Memory (sport, city) in localStorage.
2. **Layer 2, AI chat (optional, later):** the Claude version below (`chatbot/`), behind a spend cap, or a small free in-browser model. Built only if layer 1 shows people need more conversation.
The sections below describe layer 2 unless they say otherwise; the scope, gear ranking and labels apply to both.

## Scope
Answers only about racket sports, racket courts, and where to buy or rent racket-sport gear. Anything else gets a short refusal. No bookings, no payments (links out only).

## How it works
- Claude with tools over our own data (not open web): `search_venues`, `get_venue`, `list_events`, `sport_info`, `find_gear`.
- Answers come from tool results only; repeat `confirmation` / "inferred" labels; never invent a venue, price or stock.
- General how-to-start and rules questions: the sport list's own description, facts and links (`sports[].d/f/u` in `venues.json`), then model knowledge, said as general advice.
- Off-topic guard: system prompt plus a cheap classifier pass (small model).

## Memory
- Phase 1: chat history and a small profile (sport, city, skill level) in the browser's localStorage. No accounts, nothing on a server.
- Phase 2 (only if beta shows demand, own ADR): accounts and server memory (ties to social phase B in CLAUDE.md item 7c).
- Never store names, emails or exact home locations.

## Gear stores (new data)
- Sources: OSM `shop=sports` and sport-tagged shops, Overture sporting-goods categories, then specialist shops from their own public pages (`evidence` + `verified_on`). No Google Places (ADR 0005), no logins (ADR 0007).
- New seed `gear_stores.csv`: name, address, sport(s), `store_type` (`specialist` / `general_sporting_goods` / `big_box`), `services` (stringing, demo, rental), `stock_basis` (`confirmed` from the store's page, else `inferred`), `evidence`, `verified_on`.
- Ranking, most to least useful, rule-based and shown to the user:
  1. Specialist for that sport (stocks its rackets; stringing, demo or rental raise it).
  2. General sporting goods with a racket section.
  3. Big box.
  Distance breaks ties. The reply says why each store ranked where it did. No sponsored or affiliate ordering.

## Hosting and cost
- Pages is static, so the API key sits in a small serverless function (e.g. Cloudflare Worker). Per-visitor rate limit and a hard daily spend cap. Small model first; prompt caching for the tool and data prompt.
- Cost is per message; measure it in the prototype before choosing a cap.

## Risks
- Wrong or stale answers: mitigated by tools-only answers and labels; test set below.
- Cost abuse: rate limit and daily cap.
- Privacy: no server memory in phase 1; no personal data in logs.
- Gear data effort: the biggest job; start with one metro.

## Steps (cheapest first)
1. Test set: `docs/chatbot_questions.md` (30 questions with expected behaviour). DONE (draft).
2. Local prototype script (no hosting) calling Claude with the tools over `venues.json`; run the test set; note failures and cost per question.
3. Gear seed for one metro (propose LA or Bay Area) with the ranking rules.
4. After beta findings (December): hosted widget, limits, then decide on phase 2 memory.

Go/no-go after step 2: the bot answers at least 80% of the test set correctly with no invented facts, at a cost per message the owner accepts.
