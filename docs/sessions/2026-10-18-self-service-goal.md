# 2026-10-18: self-service goal added to the plan

Added the long-term goal "run itself with minimal human review, AI-assisted" to ADR 0015 (Decision) and to CLAUDE.md (mission line + "After beta" list). Framed as agentic and automated-first (owner wants minimal human review): scheduled single-job agents behind automated gates, auto-merge for low-risk classes, escalation only for risky ones, audit digest + revert + kill switch as the safety net. Docs only; nothing built.
Next: classify `docs/monthly_refresh.md` steps as mechanical vs judgment, then write the ADR for unattended scheduled jobs before automating anything that writes to the repo.
