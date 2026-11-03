# Chatbot test questions (draft, 2026-11-02)

30 questions to score a prototype. "Expect" is the behaviour that passes. Fill in the expected venue names from `venues.json` when running (the answer must come from a tool result). Pass = right facts, labels kept, nothing invented.

## Find a place (10)
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

## Watch and events (4)
11. Any tennis tournaments I can watch near Redding this fall? Expect: events from `watch_events`, links.
12. Where can I watch pro pickleball in Nevada? Expect: events or "none listed".
13. Is anything on this weekend in Bakersfield? Expect: dated events only, no guesses.
14. Where can I watch tennis on a big screen? Expect: says on-site events only today, screenings not yet covered.

## Learn about sports (6)
15. What is padel and how is it different from pickleball? Expect: general answer, marked general.
16. What sport should I try if I like tennis but want something easier on the knees? Expect: suggestions, links to places if asked.
17. What is pop tennis vs paddle tennis? Expect: correct distinction.
18. How do I get started with squash? Expect: basics, offers nearby venues.
19. What equipment do I need for racquetball? Expect: racket, eyewear, ball; no brand pushing.
20. Is badminton the same as pickleball? Expect: clear no, brief difference.

## Gear (6)
21. Where can I buy a pickleball paddle in San Diego? Expect: ranked list, specialist first, reasons shown, stock labelled confirmed or inferred.
22. Where can I get a tennis racket restrung near me (Berkeley)? Expect: stringing services only if in data.
23. Can I rent a padel racket before buying? Expect: venues listing rentals, else says unknown.
24. Cheapest place to try a squash racket? Expect: no invented prices; uses cost only if sourced.
25. Rank the racket shops in Las Vegas from most to least useful for pickleball. Expect: rule-based ranking with the why.
26. Which store has the best deals? Expect: declines to claim deals; offers ranking by relevance.

## Memory (2)
27. (after saying "I play padel in Reno, beginner") Where should I play? Expect: uses the stated profile.
28. (new session, same browser) What did I say I play? Expect: remembers from local profile; says it is stored in this browser only.

## Off-topic and safety (2)
29. Write me a cover letter. Expect: short refusal, offers racket-sport help.
30. Book me a court at 6pm tomorrow. Expect: says it cannot book, links to the venue's booking page if in data.
