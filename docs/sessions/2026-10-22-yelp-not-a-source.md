# 2026-10-22: Yelp is not a pipeline source

Question: can Yelp user comments help find courts per state? Answer: only as hand-read leads; the API is paid (few short excerpts, limited caching per secondary sources, unverified against Yelp's terms) and scraping breaks ADR 0007. No Yelp code or data exists in the project (3 seed rows cite a Yelp URL as evidence). Owner will not do hand checks, so the project does not rely on Yelp.
Changed: ADR 0017 now names review sites as out of scope for the reader. Next: nothing; revisit only if a free, terms-compliant source appears (needs an ADR amending 0007).
