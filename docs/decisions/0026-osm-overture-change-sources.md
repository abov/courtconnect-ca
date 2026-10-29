# 0026. Where the change feed gets its "what changed" for OSM and Overture

Date: 2026-10-29. Status: **proposed** (owner decides). Step 1 of ADR 0025 (the public `app/data/changes.json`, no personal data) needs a source for "a court or place appeared, closed or moved". Follow-up named in `docs/planet_scale_plan.md`. The Overture side is built as a script (below); nothing writes `changes.json` yet.

## Context
The pipeline refreshes twice a month (the extracts, then dbt). A change feed only needs to say what differs between two refreshes. Two outside sources move between them:
- **OSM** courts (`data/raw/osm_courts*.csv`, keyed by `osm_type` + `osm_id`), edited by anyone at any time.
- **Overture** places (`data/raw/overture_places.csv`, keyed by a stable GERS `id`), published as a new release roughly monthly.

The planet-scale plan listed "OSM minutely replication diffs filtered to CA/NV racket tags" as the next step.

## Options for OSM
| | What it is | New moving parts | Fits twice-monthly? |
|---|---|---|---|
| **A. Snapshot diff (recommended)** | Keep the previous `osm_courts*.csv`, diff by `(osm_type, osm_id)` against the new one after each extract: new, gone, tag changes (sport, access, fee, name), moved | None: reuses the extract that already runs | Yes, exactly the cadence of the feed |
| **B. Overpass `diff:` / `adiff:` query** | Ask the Overpass API what changed since the last refresh date, restricted to the CA/NV areas and racket tags (syntax to verify before use) | One more Overpass query, same fair-use limits as `overpass.py` | Yes; adds who/when per edit |
| **C. Minutely replication** | Follow the planet minutely `.osc` diffs, keep a sequence-number state, filter to CA/NV racket tags | A long-running or catch-up process, state file, a tool to parse change files | Overkill: we read at most twice a month and nothing here needs minute-level latency |

## Decision (proposed)
1. **OSM: option A.** Snapshot-diff the court extracts. It adds no service, no state beyond last refresh's CSV (the diff script must copy it aside before the extract overwrites it, since `data/raw` is not versioned), and no new dependency. Revisit B only if the feed needs "edited by X on date Y"; reject C unless the refresh moves to daily or faster.
2. **Overture: release-to-release diff by id** (built, `ingestion/overture_release_diff.py`). Old side is the local snapshot, new side is read from S3 with the extract's own query (`fetch_places`); kinds are `new`, `gone`, `closed`, `reopened`, `renamed`, `moved` (over 100 m). It writes `data/raw/overture_release_diff.csv`, flags ids already in `closed_places.csv`, and does not overwrite the shared raw extract.
3. **A raw diff is not yet a feed row.** Only changes that survive the dbt match (an actual venue, or an `Opening soon` pin) become `changes.json` rows, with the data's own label (`reported`, `inferred`, `confirmed`). An Overture `closed` or an OSM `gone` is a lead for a person or the refresh agent to confirm (ADR 0019), never an automatic "closed" claim: the repo's rule is that inferred data stays labelled inferred.
4. **Order of work if accepted:** (a) venue-id stability check and a first-seen date in the export (ADR 0025 prerequisites), (b) OSM snapshot diff script beside the Overture one, (c) a dbt or Python step that joins both diffs to venue ids and writes `changes.json`, (d) a "What's new" strip, only after the beta.

## Consequences
- No new dependency, service or spend. The Overture diff reads about the same slice as the normal places extract, a few percent of the release (`docs/planet_scale_benchmark.md`).
- README ADR count moves to 0026 (0023 to 0026 proposed). CLAUDE.md "After beta" favorites line gains a pointer to this ADR.
- Risk: snapshot diffs cannot see an edit made and reverted between two refreshes, and Overture `gone` also fires when a place stops matching the racket filter, not only when it closes. The `detail` column says so; the feed treats both as leads.
