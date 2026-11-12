# Ask box and chatbot: plan, test questions and UX todo

Merged 2026-11-12 from `chatbot_plan.md`, `chatbot_questions.md`, `chatbot_ux_todo.md`; each is now a section below.

## Chatbot plan (draft, 2026-11-02)

Goal: test whether a chatbot is useful to players, and what it needs. Not built yet; ADR 0033 (proposed) holds the decisions. Waits for the December beta before anything is hosted.

### Two layers (owner, 2026-11-02: free first, AI later)
1. **Layer 1, free "ask box":** no AI model, no key, no server. Rules read the sport, city, filters and intent from the question, then search `venues.json` in the browser (`app/ask.js`, test page `app/ask.html`, not linked from the main page yet; checks: `node chatbot/test_ask.js`). Costs nothing per message. Memory (sport, city) in localStorage.
2. **Layer 2, AI chat (optional, later):** the Claude version below (`chatbot/`), behind a spend cap, or a small free in-browser model. Built only if layer 1 shows people need more conversation.
The sections below describe layer 2 unless they say otherwise; the scope, gear ranking and labels apply to both.

### Scope
Answers only about racket sports, racket courts, and where to buy or rent racket-sport gear. Anything else gets a short refusal. No bookings, no payments (links out only).

### How it works
- Claude with tools over our own data (not open web): `search_venues`, `get_venue`, `list_events`, `sport_info`, `find_gear`.
- Answers come from tool results only; repeat `confirmation` / "inferred" labels; never invent a venue, price or stock.
- General how-to-start and rules questions: the sport list's own description, facts and links (`sports[].d/f/u` in `venues.json`), then model knowledge, said as general advice.
- Off-topic guard: system prompt plus a cheap classifier pass (small model).

### Memory
- Phase 1: chat history and a small profile (sport, city, skill level) in the browser's localStorage. No accounts, nothing on a server.
- Phase 2 (only if beta shows demand, own ADR): accounts and server memory (ties to social phase B in CLAUDE.md item 7c).
- Never store names, emails or exact home locations.

### Gear stores (new data)
- Sources: OSM `shop=sports` and sport-tagged shops, Overture sporting-goods categories, then specialist shops from their own public pages (`evidence` + `verified_on`). No Google Places (ADR 0005), no logins (ADR 0007).
- New seed `gear_stores.csv`: name, address, sport(s), `store_type` (`specialist` / `general_sporting_goods` / `big_box`), `services` (stringing, demo, rental), `stock_basis` (`confirmed` from the store's page, else `inferred`), `evidence`, `verified_on`.
- Ranking, most to least useful, rule-based and shown to the user:
  1. Specialist for that sport (stocks its rackets; stringing, demo or rental raise it).
  2. General sporting goods with a racket section.
  3. Big box.
  Distance breaks ties. The reply says why each store ranked where it did. No sponsored or affiliate ordering.

### Hosting and cost
- Pages is static, so the API key sits in a small serverless function (e.g. Cloudflare Worker). Per-visitor rate limit and a hard daily spend cap. Small model first; prompt caching for the tool and data prompt.
- Cost is per message; measure it in the prototype before choosing a cap.

### Risks
- Wrong or stale answers: mitigated by tools-only answers and labels; test set below.
- Cost abuse: rate limit and daily cap.
- Privacy: no server memory in phase 1; no personal data in logs.
- Gear data effort: the biggest job; start with one metro.

### Steps (cheapest first)
1. Test set: `docs/chatbot.md` (30 questions with expected behaviour). DONE (draft).
2. Local prototype script (no hosting) calling Claude with the tools over `venues.json`; run the test set; note failures and cost per question.
3. Gear seed for one metro (propose LA or Bay Area) with the ranking rules.
4. After beta findings (December): hosted widget, limits, then decide on phase 2 memory.

Go/no-go after step 2: the bot answers at least 80% of the test set correctly with no invented facts, at a cost per message the owner accepts.

## Chatbot test questions (draft, 2026-11-02)

30 questions to score a prototype. "Expect" is the behaviour that passes. Fill in the expected venue names from `venues.json` when running (the answer must come from a tool result). Pass = right facts, labels kept, nothing invented.

### Find a place (10)
1. Where can I play pickleball in Reno? Expect: venues from data, access shown.
2. Free public tennis courts near Santa Monica? Expect: only public/free-tagged, says if unknown.
3. Is there a padel court in Las Vegas? Expect: real clubs, or "none found".
4. Where can I play racquetball in San Diego? Expect: gyms/public facilities from data, with access note.
5. Any squash courts in the Bay Area open to non-members? Expect: access label respected, members-only not offered as open.
6. Where can I hit against a wall in Oakland? Expect: stand-alone wall pins and court venues with walls on site, tagged-only ones labelled.
7. Closest badminton courts to Sacramento? Expect: venues with distance or city, no invention.
8. Is there pop tennis in LA? Expect: separates pop tennis from padel.
9. Are there lit courts for evening tennis in Henderson? Expect: says lighting only if in data, else unknown.
10. Where can I play beach tennis in California? Expect: the few known locations, honest about gaps.

### Watch and events (4)
11. Any tennis tournaments I can watch near Redding this fall? Expect: events from `watch_events`, links.
12. Where can I watch pro pickleball in Nevada? Expect: events or "none listed".
13. Is anything on this weekend in Bakersfield? Expect: dated events only, no guesses.
14. Where can I watch tennis on a big screen? Expect: says on-site events only today, screenings not yet covered.

### Learn about sports (6)
15. What is padel and how is it different from pickleball? Expect: general answer, marked general.
16. What sport should I try if I like tennis but want something easier on the knees? Expect: suggestions, links to places if asked.
17. What is pop tennis vs paddle tennis? Expect: correct distinction.
18. How do I get started with squash? Expect: basics, offers nearby venues.
19. What equipment do I need for racquetball? Expect: racket, eyewear, ball; no brand pushing.
20. Is badminton the same as pickleball? Expect: clear no, brief difference.

### Gear (6)
21. Where can I buy a pickleball paddle in San Diego? Expect: ranked list, specialist first, reasons shown, stock labelled confirmed or inferred.
22. Where can I get a tennis racket restrung near me (Berkeley)? Expect: stringing services only if in data.
23. Can I rent a padel racket before buying? Expect: venues listing rentals, else says unknown.
24. Cheapest place to try a squash racket? Expect: no invented prices; uses cost only if sourced.
25. Rank the racket shops in Las Vegas from most to least useful for pickleball. Expect: rule-based ranking with the why.
26. Which store has the best deals? Expect: declines to claim deals; offers ranking by relevance.

### Memory (2)
27. (after saying "I play padel in Reno, beginner") Where should I play? Expect: uses the stated profile.
28. (new session, same browser) What did I say I play? Expect: remembers from local profile; says it is stored in this browser only.

### Off-topic and safety (2)
29. Write me a cover letter. Expect: short refusal, offers racket-sport help.
30. Book me a court at 6pm tomorrow. Expect: says it cannot book, links to the venue's booking page if in data.

## Ask box: easier to use, kinder answers (todo, 2026-11-02)

Problem: `answer()` in `app/ask.js` ends in one `REFUSE` string. Anything it can't parse (a typo, a follow-up, "hi", an unknown sport, a city we don't hold) gets the same cold "I only help with..." line, with no hint of what went wrong or what to try. Scope stays as ADR 0033 says (racket only, honest labels, no invented facts); only the tone and the way out change.

### 1. Stop one-size-fits-all refusals (`app/ask.js`)
- [x] Replace `REFUSE` with a small set of replies by cause, each one: say what I understood, say what I couldn't do, offer 2-3 things to try (as tappable chips):
  - greeting / thanks / "help" / "what can you do": friendly hello + what I can do + example chips
  - truly off-topic: "That's outside what I can help with. I'm built for racket sports, so ..." + chips
  - another sport we don't list (cricket, golf, ...): name it back, say we only cover racket sports, suggest the closest listed one
  - on-topic but unparsed (RACKET words, no sport/city): ask the one missing piece (already partly done by `clarify`)
  - frustration ("this is useless", "that's wrong"): apologize once, ask what they were after, point to "report a missing place"
- [x] Never end a reply without a next step: every `refuse`, `clarify` and empty-result answer carries chips.

### 2. Understand more of what people type
- [ ] Typos: fuzzy-match sport and city names (edit distance 1-2 on keys of 5+ letters; "pickelball", "las vagas", "racketball"). Say "Did you mean pickleball?" when the match is a guess.
- [ ] Follow-ups: remember the last sport, place and intent in the session (not only the saved profile), so "what about Reno?", "any free ones?", "and padel?" reuse the previous question.
- [ ] Unknown place: when a place isn't in `cities`, say "I don't have a city called X; try a nearby bigger one" (or list a few close ones) instead of ignoring it.
- [ ] Zip codes / "near me": ask permission for browser location (or a city) rather than refusing.
- [ ] More phrasings: "where can I play", "any courts open tonight", "I'm new to...", "lessons for my kid".

### 3. Kinder dead ends (no results)
- [ ] Empty venue/event/group result: say "not in our data yet, which doesn't mean there are none", then offer the nearest city that has some, other sports in the same city, and the community-report link so they can add it.
- [ ] Gear questions: keep the honest "no store data yet" but add something useful (places that offer lessons or clinics, the sport's gear list, what to look for).
- [ ] Booking questions: already honest; add the venue link right in the answer when a sport and city are known.

### 4. Interaction in the widget (`app/ask-widget.js`)
- [ ] Show follow-up chips under each answer (e.g. after venues: "Only free ones", "Lit at night", "Events nearby", "Another sport"), not just at intro.
- [ ] Say what I can do in the intro in one plain line instead of "Prototype. Answers come only from...": move the disclaimer to a small "How this works" link.
- [ ] Make a "Start over" / "Forget me" chip easy to find; show saved sport and city as removable chips.
- [ ] "Was this helpful? / This missed what I wanted" buttons that store the question in this browser only, plus a prefilled issue/report link the user sends themselves (no personal data in logs, ADR 0033).
- [ ] Mobile: check keyboard overlap and chip wrapping; keep 44px tap targets.

### 5. Tone guide (shared with layer 2, the AI chat)
- [ ] Write 8-10 lines in `docs/chatbot.md`: plain words, one friendly sentence max before the answer, no blame ("I couldn't match that" not "you must ask..."), never pretend to know, labels (confirmed/inferred) stay. Use it as the system prompt base if layer 2 is ever built.

### 6. Tests
- [ ] (partly done: greetings, thanks, frustration, other sports, off-topic, chips check in `chatbot/test_ask.js`) Still to add to `docs/chatbot.md` and the tests: greetings, thanks, typos, follow-ups, unknown city, other sports, frustration, and a check that no reply is the bare old REFUSE text and every non-answer has chips.
- [ ] Keep the existing "Write me a cover letter." case: still declined, now kindly.
- [ ] Run `node chatbot/test_ask.js`.

### Suggested order (cheapest first)
1. Section 1 + chips on every non-answer, plus the tests (biggest gain, `ask.js` only).
2. Follow-up memory and typo matching (section 2).
3. Dead-end help and widget follow-up chips (sections 3-4).
4. Tone guide when layer 2 is considered (section 5).
