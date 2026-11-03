# Ask box: easier to use, kinder answers (todo, 2026-11-02)

Problem: `answer()` in `app/ask.js` ends in one `REFUSE` string. Anything it can't parse (a typo, a follow-up, "hi", an unknown sport, a city we don't hold) gets the same cold "I only help with..." line, with no hint of what went wrong or what to try. Scope stays as ADR 0033 says (racket only, honest labels, no invented facts); only the tone and the way out change.

## 1. Stop one-size-fits-all refusals (`app/ask.js`)
- [x] Replace `REFUSE` with a small set of replies by cause, each one: say what I understood, say what I couldn't do, offer 2-3 things to try (as tappable chips):
  - greeting / thanks / "help" / "what can you do": friendly hello + what I can do + example chips
  - truly off-topic: "That's outside what I can help with. I'm built for racket sports, so ..." + chips
  - another sport we don't list (cricket, golf, ...): name it back, say we only cover racket sports, suggest the closest listed one
  - on-topic but unparsed (RACKET words, no sport/city): ask the one missing piece (already partly done by `clarify`)
  - frustration ("this is useless", "that's wrong"): apologize once, ask what they were after, point to "report a missing place"
- [x] Never end a reply without a next step: every `refuse`, `clarify` and empty-result answer carries chips.

## 2. Understand more of what people type
- [ ] Typos: fuzzy-match sport and city names (edit distance 1-2 on keys of 5+ letters; "pickelball", "las vagas", "racketball"). Say "Did you mean pickleball?" when the match is a guess.
- [ ] Follow-ups: remember the last sport, place and intent in the session (not only the saved profile), so "what about Reno?", "any free ones?", "and padel?" reuse the previous question.
- [ ] Unknown place: when a place isn't in `cities`, say "I don't have a city called X; try a nearby bigger one" (or list a few close ones) instead of ignoring it.
- [ ] Zip codes / "near me": ask permission for browser location (or a city) rather than refusing.
- [ ] More phrasings: "where can I play", "any courts open tonight", "I'm new to...", "lessons for my kid".

## 3. Kinder dead ends (no results)
- [ ] Empty venue/event/group result: say "not in our data yet, which doesn't mean there are none", then offer the nearest city that has some, other sports in the same city, and the community-report link so they can add it.
- [ ] Gear questions: keep the honest "no store data yet" but add something useful (places that offer lessons or clinics, the sport's gear list, what to look for).
- [ ] Booking questions: already honest; add the venue link right in the answer when a sport and city are known.

## 4. Interaction in the widget (`app/ask-widget.js`)
- [ ] Show follow-up chips under each answer (e.g. after venues: "Only free ones", "Lit at night", "Events nearby", "Another sport"), not just at intro.
- [ ] Say what I can do in the intro in one plain line instead of "Prototype. Answers come only from...": move the disclaimer to a small "How this works" link.
- [ ] Make a "Start over" / "Forget me" chip easy to find; show saved sport and city as removable chips.
- [ ] "Was this helpful? / This missed what I wanted" buttons that store the question in this browser only, plus a prefilled issue/report link the user sends themselves (no personal data in logs, ADR 0033).
- [ ] Mobile: check keyboard overlap and chip wrapping; keep 44px tap targets.

## 5. Tone guide (shared with layer 2, the AI chat)
- [ ] Write 8-10 lines in `docs/chatbot_plan.md`: plain words, one friendly sentence max before the answer, no blame ("I couldn't match that" not "you must ask..."), never pretend to know, labels (confirmed/inferred) stay. Use it as the system prompt base if layer 2 is ever built.

## 6. Tests
- [ ] (partly done: greetings, thanks, frustration, other sports, off-topic, chips check in `chatbot/test_ask.js`) Still to add to `docs/chatbot_questions.md` and the tests: greetings, thanks, typos, follow-ups, unknown city, other sports, frustration, and a check that no reply is the bare old REFUSE text and every non-answer has chips.
- [ ] Keep the existing "Write me a cover letter." case: still declined, now kindly.
- [ ] Run `node chatbot/test_ask.js`.

## Suggested order (cheapest first)
1. Section 1 + chips on every non-answer, plus the tests (biggest gain, `ask.js` only).
2. Follow-up memory and typo matching (section 2).
3. Dead-end help and widget follow-up chips (sections 3-4).
4. Tone guide when layer 2 is considered (section 5).
