# Website finder: scripts first, a model for the rest

Goal: official websites for pins that have none (`transform/seeds/venue_website_official.csv`), at the lowest token cost. PRs #822-#840 did this with a large model per metro (search, open page, judge, write a CSV row). Most of that is mechanical, so `ingestion/find_websites.py` (`make find-websites`) does it and a cheap model sees only what is left.

## Run

```bash
python ingestion/find_websites.py --region OR --city Eugene,Springfield          # real run, writes data/website_proposals/
python ingestion/find_websites.py --region OR --city Eugene --dry-run            # list the pins, no outside request
python ingestion/find_websites.py --region OR --eval                             # score the script against rows a past pass already settled
python ingestion/find_websites.py --region OR --city Eugene --hints hints.csv    # check URLs a person or model found (venue_id,url)
python ingestion/find_websites.py --region OR --city Eugene --apply              # append the auto rows to the seed
```

Filters: `--region`, `--city` (as the map shows it), `--bbox S W N E`, `--sport` (default Tennis), `--max-pins`. `--directory file.csv` (name,city,website) feeds a public school or club directory, as the CDE list did in #830. Needs the local warehouse (`make fresh-db` in a new worktree). Outputs, all git-ignored, go to `data/website_proposals/`: `proposed_rows.csv` (exact seed shape), `review_queue.csv`, `report.md`.

## What the script does (no model)

1. **Pins**: named (not `unnamed`), not home-like, no website from OSM, Overture, `manual_venues` or the seed. Display suffixes are stripped ("(northeast courts, 2 courts)", "- Gresham", "Tennis Courts").
2. **Candidate URLs**, cheapest first: `--hints`; `--directory`; Overture places within 300 m with the same name and a website; Wikidata entities with the same name and a coordinate within 2 km (property "official website", CC0); sibling pattern: schools of one district share a host suffix (`jackson.pps.net`, `bhs.beaverton.k12.or.us`), so `<slug>.<suffix>` is tried for suffixes that at least two known school sites near the pin use (DNS first, so a wrong guess costs nothing). No search engine is scraped.
3. **Fetch** (plain HTTP, project User-Agent from `ingestion/useragent.py`, robots.txt respected, 2 s per host, 400 KB cap, 14-day cache in `data/reader_cache/`). A dead deep link is retried at the site root.
4. **Score by code**: every distinctive word of the name is in the page title / first heading / site name; a school level (high, middle, elementary) must match, so a district homepage or a sibling school never passes; a place-kind word alone ("College") may be missing; the pin's city, or street number and street, is on the page (or the candidate came from a coordinate-checked source); no social, listing or directory host; a park page must be on a government domain; no redirect to another site.
5. **Tiers**: `auto` (all checks pass, score >= 0.85) becomes a seed row whose evidence names the method, the checks and the candidate source, and whether the page mentions tennis (the page is a homepage, court access is not confirmed). Everything else goes to `review_queue.csv` with the pin facts, the best candidate, the failed checks, a 500-character page extract and the other URLs tried.

An `auto` row never goes to a model. A model never writes a seed row: it answers the queue, and its answers pass through the same page checks again (`--hints`).

## Measured (2026-11-17)

`--eval` hides each already-seeded pin's own website and tries to find it again. Portland metro, 30 pins from #840 (Tennis, region OR):

| Mode | Resolved by script | Right host vs the past pass | Left for a model |
|---|---|---|---|
| Warm (sibling schools' sites known, the normal case after the first pass in a district) | 22 of 30 (73%) | 22 of 22 | 8 |
| Cold (no sibling site known) | 4 of 30 (13%) | 4 of 4 | 26 |

Live dry run on Eugene and Springfield (18 pins, no hints, nothing known about the schools): 2 resolved by the script (11%), 1 candidate with a failed check, 14 with no candidate. So the script cuts the model's work a lot where a district pattern or Wikidata exists, and not at all where discovery needs a web search: discovery, not checking, is the expensive part, which is why the queue separates the two.

Two defects the eval caught are fixed and kept as rules: a district homepage ("Beaverton School District") matching "Beaverton High School" (fixed by the school-level rule) and a `.com` fan page for a park (fixed by the government-domain rule).

## Who handles the leftover (recommendation, not measured here)

- **No candidate URL** (needs web search): Sonnet 5.5, or the cheapest model that can call search. Task: for each queue row print one URL or `none`, written to a `hints.csv`; do not judge it. Then rerun with `--hints`; the script does the checking, so the model's mistakes are caught by code.
- **Candidate found, a check failed** (the queue has the page extract, no browsing needed): Haiku 5.5. Task: answer `same place` / `different place` / `unsure` with a one-line reason per row, from the extract only. `same place` rows are re-run through `--hints` with the failed check named in the evidence; `unsure` go to a person.
- Keep a large model for rows where Haiku is `unsure` and the place matters (a resort, a club with several sites). Expect that to be a few rows a metro.

Tokens: the queue row is about 1 KB, against a full search-and-read per pin before. Per-metro token numbers will show in `make ops-metrics` after the first real passes; fill the table above from them.

## Rules (CLAUDE.md, ADR 0005, 0007)

Public pages only; no owner logins; project User-Agent only; no Google Places; no directory or listing sites as the source of a website (Pickleheads, Yelp, Facebook and similar hosts are rejected). The seed stays `evidence` + `verified_on` for every row; the script labels what it inferred (name match, source, score) and never says court access is confirmed. Recheck pages later with `make check-pages`; dead domains show up in `make check-websites`.

## Next generators (not built)

State school directories as `--directory` input (CDE for California was done by hand in #830; Oregon ODE and Washington OSPI have the same lists); city parks pages by known URL patterns (`seattle.gov/parks/parks/<slug>`), learned like the school suffixes.
