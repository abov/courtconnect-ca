# 0015. Mission, sport discovery and a social phase

Date: 2026-10-15. Status: accepted (2026-10-15) for the mission and phases A; phase B (own accounts) needs its own ADR before any work.

## Context
CourtConnect began as a venue finder. The owner wants one overall goal that covers why it exists: people should be able to find every racket sport and court in the region, try sports they have not played, and get together with friends or others to play. Two gaps stand out:
- **Pickleball crowds out the rest.** Many parks are tagged for both tennis and pickleball, and pickleball has the most venues, so the map and the sport picker feel like a pickleball map. Pickleball is welcome, but tennis is a strong, established sport that should stay visible, and lesser-known sports (padel, squash, badminton, table tennis, racquetball, Pop Tennis, paddleball, Basque pelota and others) are hard to discover.
- **Finding people is the next question.** After "where can I play?" comes "who can I play with?". The project already links out to groups (ADR 0009 social, 0010 WhatsApp, 0012 Meetup/Partiful) but has no view built around that.

## Decision
- **Mission:** help people in California and Nevada find every place to play or watch racket sports, discover sports they have not tried, and get together with others to play. "Every place" means every place found in public sources, labelled by how sure we are (ADR 0007); it is not a promise of completeness.
- **Sport discovery (after the beta):** a short "Try something new" card per sport (what it is, why it is fun, how easy it is to start, nearest place to try it), lesser-known sports given room in the picker and popups, and watch events for those sports too, not only tennis and pickleball.
- **Tennis stays visible:** tennis keeps its own pin look and is never hidden inside a pickleball pin; shared courts say both sports in the popup ("Tennis + Pickleball lines"); the sport picker is not ordered by venue count; Watch mode keeps featuring tennis events and clubs.
- **Social phase A (link-out, fits today's rules):** a "Find people to play with" view built from groups that already exist: club ladders, open-play times, beginner clinics, try-it nights, Meetup/WhatsApp/Partiful groups. Same rules as other link-outs: public pages only, `verified_on` + evidence, no logins.
- **Social phase B (later, not decided):** CourtConnect's own accounts, partner matching or event posting. This stores user data and needs moderation, safety, privacy terms and a change to "link out, never transact". It gets its own ADR, and only if beta findings (2026-10-29..11-01) show people want it.
- **Order:** finish the beta round first; rank sport discovery, tennis visibility and social phase A with the beta findings (RICE, `docs/feedback_findings.md`); phase B after that, if at all.

## Consequences
More data work per sport (intro text, try-it events, group links), kept fresh by the twice-monthly runbook. Visual changes overlap with the paused polish plan (`docs/ux_polish.md`, PR 6 sport glyph pins), so they are planned together. Until phase B has an ADR, CourtConnect stores no user accounts or personal data.
