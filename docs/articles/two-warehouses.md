# I built for two warehouses, then deleted one

*Draft, 2026-10-29. Facts come from [ADR 0001](../decisions/0001-duckdb-first-then-snowflake.md), [ADR 0018](../decisions/0018-duckdb-only.md) and the repository history.*

When I started CourtConnect I made a decision that sounds careful: develop on DuckDB, deploy to Snowflake, and keep every model runnable on both. The rule was "portable SQL, identical results". [ADR 0001](../decisions/0001-duckdb-first-then-snowflake.md) wrote it down.

On 2026-10-14 I retired Snowflake. This is what the next week taught me about portability rules.

## The rule had a running cost

Keeping SQL portable is not free. It shows up in small ways:

- Macros wrapped in `adapter.dispatch` so a function could have a DuckDB version and a "default" one.
- A reflex to avoid DuckDB features (richer list, string and spatial functions) because they might not exist elsewhere.
- Config, scripts and docs for two targets: a Snowflake profile, a setup script, a `--target snowflake` branch in the loader, two Snowflake packages and a block of environment keys.

None of it hurt on any given day. That is how a rule like this survives long after its reason has gone.

## What I found when I looked

After the retirement, the project said "DuckDB only" in its instructions, but no decision record said so, so ADR 0001 still read as current. I wrote [ADR 0018](../decisions/0018-duckdb-only.md) and, before deciding anything, grepped for what was left. The audit was more revealing than the decision:

- No workflow touched Snowflake: CI was DuckDB only. The map reads a JSON file exported from DuckDB. The refresh ran on DuckDB. **Nothing in the daily path touched Snowflake.**
- The "portable" macro file had a DuckDB version and a default version of each macro, and **no Snowflake-specific version**. The dispatch only separated DuckDB from "anything else".
- One model carried a Snowflake-only block for a geography column that no downstream model or export ever read.

So "runs unchanged on both engines" had been a claim, not a property. Without a test in CI, a portability promise decays quietly; it can be true on the day you write it and false a month later with nothing failing.

## The decision, in two halves

ADR 0018 splits the question:

1. **Remove the dead code?** The conservative plan was to keep it dormant and delete it in one PR after the December beta. Dead code is easy to bring back from git history but harder to reason about while it half works.
2. **Relax the rule?** Yes, immediately. New models and macros no longer need a Snowflake-safe form. The existing `adapter.dispatch` macros stay, because rewriting working code is churn, but plain DuckDB SQL is fine in new work.

A few days later I brought the removal forward and did it in one change ([PR #304](https://github.com/abov/courtconnect-ca/pull/304), 2026-10-21): the profile, the setup script, the make target, the loader branch, the geography column, both packages and the environment keys. The ADR's plan for checking it was a DuckDB build to confirm nothing changed.

## What it costs, and what it does not

The honest downside is written into the ADR: if the project ever needs a cloud warehouse, portability has to be rebuilt and re-tested, and that would need a new decision record. I chose to pay that later, if at all, instead of paying a small tax every day for an option nobody was exercising.

What it does not cost is capability. The data we keep is small (about 10,000 venues). DuckDB queries the large public Overture files on S3 in place and fetched about 743 MB of 39.6 GB for the real extracts ([benchmark](../planet_scale_benchmark.md)). The warehouse never needed to be big; the sources did.

## What I would take from this

- **A portability rule needs a test, or it is a hope.** If CI does not run the second engine, you are not portable; you are optimistic.
- **Tie every constraint to its reason.** "Keep SQL portable" was there to keep a Snowflake deployment possible. When that went away, the rule should have been reviewed the same day.
- **Record the reversal.** For three days (2026-10-14 to 10-17) the project's instructions and its decision record disagreed. A superseding ADR closed the gap.
- **Delete early once it is safe.** Dormant code that nothing exercises is a liability, and git already remembers it.

*The decisions: [ADR 0001](../decisions/0001-duckdb-first-then-snowflake.md) (superseded) and [ADR 0018](../decisions/0018-duckdb-only.md).*
