# 0029. Rename the product to RacketConnect

Date: 2026-11-02. Status: accepted (owner, chat 2026-11-02).

## Context
"CourtConnect CalNeva" names a region (ADR 0014) and a place, not the sport family. "Court" alone reads as basketball or volleyball, and "CalNeva" will be outgrown if the scope grows (ADR 0028, proposed). The owner wants people to see at once that these are racket sports.

## Decision
- **Display name: RacketConnect.** No region in the name; the region is a sentence in the description (`BRAND` and `REGION` in `app/index.html`). Tagline stays "where to play racket sports".
- **Changed:** app pages, manifest, `llms.txt`, share card, dbt exposure label and model docs, README, CLAUDE.md, docs, the six cloud routines' titles and prompt text.
- **Kept (identifiers, not display):** repo `abov/courtconnect-ca`, data repo `abov/courtconnect-data`, Pages URL, `courtconnect.duckdb`, dbt project/profile/macro namespace and the `courtconnect_map` exposure id, `COURTCONNECT_*` env vars, the User-Agent string, GoatCounter site `courts`. Renaming them breaks fresh worktrees, CI, the routines' git sources and published links for no visitor-facing gain. Revisit with a custom domain, which would decouple the brand from the repo name.
- **Not rewritten:** older ADRs, `docs/archive/`, `docs/sessions/` stay as written; "CourtConnect" and "CalNeva" there are history. "CalNeva" remains the name of the CA + NV scope in ADR 0014.

## Open
- Check the name and a domain are free before announcing it. Not done.
- Ask the name question in the beta (`docs/feedback_round.md`).
