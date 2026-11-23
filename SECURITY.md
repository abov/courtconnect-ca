# Security policy

RacketConnect is a static map of racket-sport venues (`app/`) built from public data by a Python and dbt pipeline. It has no accounts, no bookings or payments, and stores no personal data. What a flaw could do: put a wrong or hostile link or fact on the public map, leak a credential, or let an automated agent change data without the checks that should stop it.

## Reporting a vulnerability
Use GitHub's private report: **Security tab, "Report a vulnerability"** (https://github.com/abov/courtconnect-ca/security/advisories/new). Please do not open a public issue or PR for a security problem, and do not put personal contact details in a report you want kept private beyond what GitHub already holds.

This is a one-person project run partly by AI agents, so there is no bug bounty and no guaranteed response time. The aim is to acknowledge a report within 7 days and fix or explain within 30. Reports are credited unless you ask otherwise.

## In scope
- The live site and `app/` (script injection, unsafe links, anything that renders untrusted text without escaping).
- The GitHub Actions workflows and the agent merge gate ([`docs/merge_gate_threat_model.md`](docs/merge_gate_threat_model.md), ADR 0019): a way for a PR, an issue or a fork to get a change merged without the gate's checks.
- Prompt injection: text on a venue page, in an issue or in a PR that steers an agent into editing data, calling out, or leaking secrets.
- Leaked credentials, tokens or private data in the repo or its history.

## Out of scope
- Wrong or out-of-date venue facts. Use the "report a venue" or "suggest a change" issue forms; the map labels inferred data as inferred.
- Findings against third-party sites the map links to.
- Denial of service, volume or rate testing, and automated scanning of the live site.
- Social engineering of the owner or contributors.

## How the project protects itself today
- **Secrets:** credentials live in `.env`, which is never committed, read or printed (`.env.example` lists the keys). GitHub secret scanning and push protection are on; a Claude Code hook (`.claude/hooks/guard.py`) blocks reads of `.env`.
- **Dependencies:** GitHub dependency alerts and Dependabot security updates are on, and `.github/dependabot.yml` opens weekly grouped version-update PRs for `requirements.txt`, `dashboard/` and the Actions.
- **Changes:** every change is a PR and `dbt-build` must pass. Agents never merge directly: a deterministic gate with path allowlists, diff caps and a kill switch decides (ADR 0019). Issue text and fetched pages are treated as data, never instructions.
- **Watching:** a weekly audit workflow (`.github/workflows/weekly-audit.yml`) lists last week's merged PRs that touched guarded paths or merged without a green `dbt-build`, adds a sample to spot-check, and fails if the scheduled chain has stopped for 20 days.
- **Privacy:** the pipeline sends only the project User-Agent to outside services, never the owner's email or contact details, and does not store inferred street addresses for home-like places.

Known gaps are written down, not hidden: see "Gaps" in [`docs/merge_gate_threat_model.md`](docs/merge_gate_threat_model.md).
