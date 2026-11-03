# 2026-11-02 Chatbot: free ask box

Plan + ADR 0033 (proposed) for a racket-only chatbot in two layers. Layer 1 built: `app/ask.js` + unlinked test page `app/ask.html`, no AI model, answers only from `venues.json` (venues, wall pins, events, social groups, sport list descriptions); 35/35 checks pass (`node chatbot/test_ask.js`, the 30 questions in `docs/chatbot_questions.md` plus 5 for other states/social/walls). Layer 2 prototype (`chatbot/tools.py`, `run.py`, Claude + tools, Haiku, spend cap) written but never run: needs `ANTHROPIC_API_KEY` credit.
Not checked: the page in a browser; answer quality beyond key-phrase checks. Data gaps seen: gear stores (no data, bot says so), 0 badminton in Sacramento.
Next: owner tries `app/ask.html`; wording/ranking tweaks; gear seed for one metro; decide on layer 2.
