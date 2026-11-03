# 0033. Chatbot: racket-only, tools over our own data

Date: 2026-11-02. Status: accepted (2026-11-02). Separate from ADR 0017 (LLM page reader): that reads venue pages to fill the data; this answers visitors' questions from it.

## Context
The owner wants to test whether a chatbot helps players find places to play, learn about racket sports and find gear. Plan: `docs/chatbot_plan.md`. We have curated venue, event, social-group and sport data (CA, NV, OR, WA, HI) but no gear-store data.

## Decision
- **Scope:** only racket sports, racket courts and gear shops or rentals for them. Other topics are refused briefly.
- **Grounding:** the bot answers from tools over our own data (`venues.json`, events, sports sheet, a new `gear_stores.csv`), not from live web search. It repeats confirmed/inferred labels and never invents a venue, price or stock. General sport advice is marked as general.
- **Memory:** phase 1 keeps history and a small preference profile in the visitor's browser only. Server-side memory needs accounts and its own ADR.
- **Gear ranking:** rule-based and shown to the user (specialist, then general sporting goods, then big box; services and distance break ties). No sponsored or affiliate ordering.
- **Sources:** Overture + OSM and public pages only (ADR 0005, 0007).
- **Cost:** API key only in a serverless function, per-visitor rate limit, hard daily spend cap. Prototype locally first; hosting waits for the December beta findings.
- **Two layers (owner, 2026-11-02):** layer 1 is a free rule-based ask box in the browser (no model, no key, no server); layer 2 is the AI chat, built only if layer 1 shows a need. Scope, labels and gear ranking are the same in both.
- **Links out only:** no bookings or payments.

## Consequences
Answers are limited to what we have curated, so coverage gaps show up as "I don't know" (honest, less impressive). Gear data is new work. Needs an API budget the owner accepts. If the prototype fails the go/no-go in the plan, we stop and keep the question set as a search-UX test.
